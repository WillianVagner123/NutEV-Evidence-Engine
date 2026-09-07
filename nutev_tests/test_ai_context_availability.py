from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"
if str(WEB) not in sys.path:
    sys.path.insert(0, str(WEB))

import secure_server


def test_agent_context_status_is_explicit_when_bundle_is_absent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(secure_server, "APP_ROOT", tmp_path)

    status = secure_server._agent_context_status()

    assert status["status"] == "not_materialized"
    assert status["available"] is False
    assert status["base_url"] is None
    assert status["available_files"] == []
    assert status["missing_files"] == list(secure_server.AGENT_CONTEXT_REQUIRED_FILES)
    assert "no scientific state is inferred" in str(status["semantics"])


def test_agent_context_status_only_becomes_available_with_complete_bundle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(secure_server, "APP_ROOT", tmp_path)
    context_root = tmp_path / "agent-context" / "article1"
    context_root.mkdir(parents=True)

    for name in secure_server.AGENT_CONTEXT_REQUIRED_FILES[:-1]:
        (context_root / name).write_text("{}\n", encoding="utf-8")

    partial = secure_server._agent_context_status()
    assert partial["available"] is False
    assert partial["missing_files"] == [secure_server.AGENT_CONTEXT_REQUIRED_FILES[-1]]

    (context_root / secure_server.AGENT_CONTEXT_REQUIRED_FILES[-1]).write_text("{}\n", encoding="utf-8")
    complete = secure_server._agent_context_status()

    assert complete["status"] == "available"
    assert complete["available"] is True
    assert complete["missing_files"] == []
    assert complete["base_url"] == "/agent-context/article1/"


def test_ai_context_ui_checks_availability_before_static_artifacts() -> None:
    js = (WEB / "ai-context.js").read_text(encoding="utf-8")
    server = (WEB / "secure_server.py").read_text(encoding="utf-8")

    status_endpoint = "/api/agent-context/article1/status"
    manifest = "/agent-context/article1/CONTEXT_MANIFEST.json"
    search_state = "/agent-context/article1/SEARCH_STATE.json"

    assert status_endpoint in server
    assert status_endpoint in js
    assert "if(!availability.available){renderUnavailable(availability);return}" in js
    assert js.index(status_endpoint) < js.index(manifest)
    assert js.index(status_endpoint) < js.index(search_state)
    assert "Nenhum estado científico foi inferido ou fabricado" in js
