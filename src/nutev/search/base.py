from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol

PROVIDER_STATUSES = {"completed", "partial", "failed", "skipped", "empty"}

_SECRET_PARAM = re.compile(
    r"((?:api_?key|apikey|key|token|secret|password|cx)=)[^&\s'\"]+",
    re.IGNORECASE,
)


def redact_secrets(text: object) -> str:
    """Strip API keys/tokens from query-string-bearing text before it is logged.

    Providers that pass credentials as URL query params (Google PSE, SerpAPI,
    Brave) leak them through requests' exception strings, which otherwise end up
    verbatim in 07_logs/provider_failures.csv and run events. This masks the
    value of any ``key=``/``api_key=``/``token=`` style parameter.
    """
    return _SECRET_PARAM.sub(r"\1REDACTED", str(text))


@dataclass
class ProviderResult:
    provider: str
    query: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    total_found: int | None = None
    total_returned: int = 0
    status: str = "completed"
    error: str | None = None
    checkpoint_path: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in PROVIDER_STATUSES:
            raise ValueError(f"invalid provider status: {self.status}")
        self.total_returned = int(self.total_returned or len(self.rows or []))
        if self.status == "completed" and self.total_returned == 0 and self.total_found in {0, None}:
            self.status = "empty"


class ProviderClient(Protocol):
    name: str

    def search(
        self,
        query: str,
        *,
        limit: int,
        context: dict[str, Any] | None = None,
    ) -> ProviderResult:
        ...
