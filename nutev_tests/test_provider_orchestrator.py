from __future__ import annotations

from nutev.search.provider_orchestrator import search_provider


def test_google_without_key_is_skipped(monkeypatch, tmp_path):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
    result = search_provider(provider="google_pse", query="x", workstream="busca1", limit=10, checkpoint_dir=tmp_path, logs_dir=tmp_path, run_id="run")
    assert result.status == "skipped"
    assert "missing" in (result.error or "")
    assert (tmp_path / "provider_failures.csv").exists()


def test_provider_exception_is_failed(monkeypatch, tmp_path):
    import nutev.search.provider_orchestrator as po

    monkeypatch.setattr(po, "search_europepmc", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("timeout")))
    result = search_provider(provider="europepmc", query="x", workstream="busca1", limit=10, checkpoint_dir=tmp_path, logs_dir=tmp_path, run_id="run")
    assert result.status == "failed"
    assert "timeout" in (result.error or "")
