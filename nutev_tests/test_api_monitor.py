from __future__ import annotations

import json

import pytest

from nutev.api.loaders import summarize_run_events, tail_jsonl


def _write_events(path, n):
    path.write_text(
        "\n".join(
            json.dumps({"run_id": "r1", "event_at": f"2026-06-17T00:00:{i:02d}Z", "event_kind": "progress", "stage": f"s{i}", "message": f"m{i}"})
            for i in range(n)
        ),
        encoding="utf-8",
    )


def test_tail_jsonl_tail_mode(tmp_path):
    p = tmp_path / "run_events.jsonl"
    _write_events(p, 10)
    r = tail_jsonl(p, limit=3, offset=0)
    assert r["available"] and r["total"] == 10
    assert [e["stage"] for e in r["items"]] == ["s7", "s8", "s9"]  # last 3
    assert r["last_stage"] == "s9" and r["run_id"] == "r1"


def test_tail_jsonl_incremental(tmp_path):
    p = tmp_path / "run_events.jsonl"
    _write_events(p, 10)
    r = tail_jsonl(p, limit=100, offset=7)  # only events recorded after line 7
    assert [e["stage"] for e in r["items"]] == ["s7", "s8", "s9"]
    assert r["total"] == 10


def test_tail_jsonl_offset_beyond_eof_returns_tail(tmp_path):
    p = tmp_path / "run_events.jsonl"
    _write_events(p, 5)
    r = tail_jsonl(p, limit=2, offset=999)  # rotated / fresh run -> resync to tail
    assert [e["stage"] for e in r["items"]] == ["s3", "s4"]


def test_tail_jsonl_missing(tmp_path):
    assert tail_jsonl(tmp_path / "nope.jsonl", limit=10, offset=0) == {"available": False, "total": 0, "offset": 0, "items": []}


def test_summarize_run_events(tmp_path):
    p = tmp_path / "run_events.jsonl"
    rows = [
        {"stage": "provider_completed", "event_kind": "progress", "meta_json": {"total_returned": 5, "total_found": 10}},
        {"stage": "provider_completed", "event_kind": "progress", "meta_json": {"total_returned": 3, "total_found": 3}},
        {"stage": "provider_empty", "event_kind": "progress", "meta_json": {"total_returned": 0, "total_found": 0}},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    s = summarize_run_events(p)
    assert s["available"] and s["total"] == 3
    assert s["stages"]["provider_completed"] == 2 and s["stages"]["provider_empty"] == 1
    assert s["rows_returned"] == 8 and s["rows_found"] == 13
    assert s["last_stage"] == "provider_empty"


def test_summarize_run_events_missing(tmp_path):
    s = summarize_run_events(tmp_path / "nope.jsonl")
    assert s["available"] is False and s["total"] == 0 and s["stages"] == {} and s["download"] is None


def test_summarize_run_events_download_position(tmp_path):
    p = tmp_path / "run_events.jsonl"
    base = [
        {"stage": "download_started", "meta_json": {"total": 100}},
        {"stage": "download_progress", "meta_json": {"done": 40, "total": 100}},
    ]
    p.write_text("\n".join(json.dumps(r) for r in base), encoding="utf-8")
    assert summarize_run_events(p)["download"] == {"done": 40, "total": 100}
    # download_completed clears the live position
    p.write_text("\n".join(json.dumps(r) for r in [*base, {"stage": "download_completed", "meta_json": {"downloaded": 10}}]), encoding="utf-8")
    assert summarize_run_events(p)["download"] is None


def test_run_events_route_and_dashboard(tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from nutev.api.server import create_app

    logs = tmp_path / "07_logs"
    logs.mkdir()
    _write_events(logs / "run_events.jsonl", 4)
    client = TestClient(create_app(tmp_path))

    resp = client.get("/api/run-events?limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 4 and len(data["items"]) == 2

    home = client.get("/")
    assert home.status_code == 200 and "run-events" in home.text  # live dashboard wired
    assert "Rodar pipeline" in home.text  # Play button present


def test_run_control_idle_and_validation(tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from nutev.api.server import create_app

    client = TestClient(create_app(tmp_path))
    # idle before any run
    status = client.get("/api/run/status").json()
    assert status["running"] is False and status["pid"] is None
    # allowlist rejects unknown workstreams (no subprocess is spawned)
    bad = client.post("/api/run", json={"workstreams": ["bad; rm -rf /"]})
    assert bad.status_code == 422
    # stopping with nothing running is a safe no-op
    assert client.post("/api/run/stop").json()["stopped"] is False


def test_run_control_concurrent_guard(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    import subprocess

    from fastapi.testclient import TestClient

    from nutev.api.server import create_app

    class FakeProc:  # a "running" process: poll() never returns a code
        pid = 4242

        def poll(self):
            return None

        def terminate(self):
            pass

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: FakeProc())
    client = TestClient(create_app(tmp_path))
    first = client.post("/api/run", json={"workstreams": ["busca1"]})
    assert first.status_code == 200 and first.json()["running"] is True
    # second concurrent start is rejected by the lock+check
    assert client.post("/api/run", json={"workstreams": ["busca1"]}).status_code == 409
    # a tracked running proc can be stopped
    assert client.post("/api/run/stop").json()["stopped"] is True
