"""Automatic chat-client selection for the NutEV retrieval-augmented ask layer.

Backend selection is automatic and side-effect free at import time:

* OpenAI is used when ``OPENAI_API_KEY`` is set (plain ``urllib`` HTTP, no SDK).
* Anthropic is used when ``ANTHROPIC_API_KEY`` is set (``langchain_anthropic``
  imported lazily inside the client so importing this module never requires it).
* Otherwise there is no client and callers fall back to offline retrieval.

When ``NUTEV_DISABLE_NETWORK=1`` no network-backed client is ever returned.
"""

from __future__ import annotations

import json
import os
from typing import Protocol, runtime_checkable
from urllib import request

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 60


@runtime_checkable
class ChatClient(Protocol):
    """Minimal protocol every chat backend implements."""

    def chat(self, system: str, user: str) -> str:
        """Return the assistant reply for a system + user prompt pair."""
        ...


def _openai_model() -> str:
    return (
        os.environ.get("NUTEV_OPENAI_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or DEFAULT_OPENAI_MODEL
    )


def _anthropic_model() -> str:
    return (
        os.environ.get("NUTEV_ANTHROPIC_MODEL")
        or os.environ.get("ANTHROPIC_MODEL")
        or DEFAULT_ANTHROPIC_MODEL
    )


class OpenAIChatClient:
    """OpenAI chat backend using ``urllib`` (no third-party SDK)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str = OPENAI_ENDPOINT,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or _openai_model()
        self.endpoint = endpoint
        self.timeout = timeout

    def chat(self, system: str, user: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.0,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
            response = json.loads(resp.read().decode("utf-8"))
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Unexpected OpenAI response shape") from exc
        if not isinstance(content, str):
            raise ValueError("OpenAI message content is not a string")
        return content


class AnthropicChatClient:
    """Anthropic chat backend backed by ``langchain_anthropic`` (lazy import)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or _anthropic_model()
        self._llm = None

    def _client(self):
        if self._llm is None:
            # Imported lazily so this module stays import-safe and test-friendly
            # even when langchain_anthropic is not installed.
            from langchain_anthropic import ChatAnthropic

            self._llm = ChatAnthropic(
                model=self.model,
                anthropic_api_key=self.api_key,
                temperature=0.0,
            )
        return self._llm

    def chat(self, system: str, user: str) -> str:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        messages = [
            ("system", system),
            ("human", user),
        ]
        result = self._client().invoke(messages)
        content = getattr(result, "content", result)
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    parts.append(str(block.get("text", "")))
                else:
                    parts.append(str(block))
            return "".join(parts)
        return str(content)


def get_chat_client(backend: str = "auto") -> object | None:
    """Return a chat client, or ``None`` for offline.

    ``backend`` may be ``"auto"`` (default; OpenAI -> Anthropic -> offline),
    ``"openai"``, ``"anthropic"`` or ``"offline"``. A forced backend whose API
    key is missing yields ``None`` (offline). ``NUTEV_DISABLE_NETWORK=1`` always
    forces offline.
    """

    if backend == "offline" or os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return None
    if backend == "openai":
        return OpenAIChatClient() if os.environ.get("OPENAI_API_KEY") else None
    if backend == "anthropic":
        return AnthropicChatClient() if os.environ.get("ANTHROPIC_API_KEY") else None
    # auto
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIChatClient()
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicChatClient()
    return None


def describe_backend(backend: str = "auto") -> str:
    """Return a stable human-readable label for the active/selected backend."""

    if backend == "offline" or os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return "offline"
    if backend == "openai":
        return f"openai:{_openai_model()}" if os.environ.get("OPENAI_API_KEY") else "offline"
    if backend == "anthropic":
        return f"anthropic:{_anthropic_model()}" if os.environ.get("ANTHROPIC_API_KEY") else "offline"
    if os.environ.get("OPENAI_API_KEY"):
        return f"openai:{_openai_model()}"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return f"anthropic:{_anthropic_model()}"
    return "offline"
