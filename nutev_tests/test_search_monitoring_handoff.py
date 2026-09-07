from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def load_secure_server():
    sys.path.insert(0, str(WEB))
    spec = importlib.util.spec_from_file_location(
        "nutev_secure_server_monitoring_test",
        WEB / "secure_server.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_monitoring_handoff_stays_inside_the_single_search_event_bus() -> None:
    events = read("search-events.js")
    ui = read("search-monitoring-ui.js")

    assert "import'./search-monitoring-ui.js';" in events
    assert events.count("window.fetch=") == 1
    assert "window.fetch=" not in ui
    assert "abandonedJobs" in events
    assert "abandonJob" in events
    assert "abandonedResponse" in events
    assert "search_monitoring_abandoned" in events
    assert "__NUTEV_MONITORING_ABANDONED__" in events
    assert "emit('nutev:search-monitoring-abandoned'" in events
    assert "if(jobId&&abandonedJobs.has(jobId))return abandonedResponse(jobId);" in events
    assert "if(jobId&&abandonedJobs.has(jobId))return;" in events


def test_monitoring_handoff_is_explicitly_non_destructive_in_the_ui() -> None:
    ui = read("search-monitoring-ui.js")
    css = read("search-ux.css")

    assert "Parar acompanhamento e fazer outra busca" in ui
    assert "A execução no servidor não é cancelada" in ui
    assert "A busca continua no servidor" in ui
    assert "Minhas buscas" in ui
    assert "window.NutEVSearchEvents?.abandonJob" in ui
    assert "new MutationObserver" in ui
    assert "#searchProgress" in ui
    assert ".search-monitor-actions" in css
    assert ".search-monitoring-detached" in css


def test_server_watcher_persists_owner_after_completion_without_browser_polling(monkeypatch) -> None:
    secure = load_secure_server()
    states = iter(
        [
            {"status": "running", "search_id": None},
            {"status": "completed", "search_id": "search-123"},
        ]
    )
    recorded: list[tuple[str, str]] = []
    statuses: list[tuple[str, str]] = []

    monkeypatch.setattr(secure, "_load_search_job", lambda _job_id: next(states))
    monkeypatch.setattr(
        secure,
        "record_search_owner",
        lambda search_id, owner_scope: recorded.append((search_id, owner_scope)),
    )
    monkeypatch.setattr(
        secure,
        "_mark_job_ownership_status",
        lambda job_id, status: statuses.append((job_id, status)),
    )
    monkeypatch.setattr(secure.time, "sleep", lambda _seconds: None)

    secure._persist_job_owner_when_terminal("job-123", "owner-scope")

    assert recorded == [("search-123", "owner-scope")]
    assert statuses == [("job-123", "recorded")]


def test_server_watcher_does_not_publish_failed_job_to_history(monkeypatch) -> None:
    secure = load_secure_server()
    recorded: list[tuple[str, str]] = []
    statuses: list[tuple[str, str]] = []

    monkeypatch.setattr(
        secure,
        "_load_search_job",
        lambda _job_id: {"status": "failed", "search_id": "search-failed"},
    )
    monkeypatch.setattr(
        secure,
        "record_search_owner",
        lambda search_id, owner_scope: recorded.append((search_id, owner_scope)),
    )
    monkeypatch.setattr(
        secure,
        "_mark_job_ownership_status",
        lambda job_id, status: statuses.append((job_id, status)),
    )

    secure._persist_job_owner_when_terminal("job-failed", "owner-scope")

    assert recorded == []
    assert statuses == [("job-failed", "not_recorded_failed_job")]


def test_job_submission_starts_owner_watch_after_session_binding_is_known() -> None:
    server = read("secure_server.py")

    owner_assignment = "_JOB_OWNERS[job_id] = owner_scope"
    watch_start = "_start_job_owner_watch(job_id, owner_scope)"
    assert owner_assignment in server
    assert watch_start in server
    assert server.index(owner_assignment) < server.index(watch_start)
    assert "target=_persist_job_owner_when_terminal" in server
    assert "daemon=True" in server


def test_monitoring_handoff_does_not_gain_scientific_authority() -> None:
    combined = (read("search-events.js") + read("search-monitoring-ui.js")).casefold()

    for forbidden in (
        "grade",
        "risk of bias",
        "certeza da evidência",
        "recomendação clínica",
        "eligibility",
    ):
        assert forbidden not in combined
