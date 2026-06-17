from __future__ import annotations

from nutev.search.provider_orchestrator import search_provider


def test_unsupported_provider_is_skipped(tmp_path):
    # Removed paid web providers (google/serpapi/brave) are now unsupported and
    # must be skipped gracefully rather than crash the orchestrator.
    result = search_provider(provider="brave", query="x", workstream="busca1", limit=10, checkpoint_dir=tmp_path, logs_dir=tmp_path, run_id="run")
    assert result.status == "skipped"
    assert "unsupported" in (result.error or "")
    assert (tmp_path / "provider_failures.csv").exists()


def test_provider_exception_is_failed(monkeypatch, tmp_path):
    import nutev.search.provider_orchestrator as po

    monkeypatch.setattr(po, "search_europepmc", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("timeout")))
    result = search_provider(provider="europepmc", query="x", workstream="busca1", limit=10, checkpoint_dir=tmp_path, logs_dir=tmp_path, run_id="run")
    assert result.status == "failed"
    assert "timeout" in (result.error or "")
