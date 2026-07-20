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


def test_stamp_retrieved_at_sets_missing_and_preserves_existing():
    from nutev.search.base import ProviderResult
    from nutev.search.provider_orchestrator import _stamp_retrieved_at

    result = ProviderResult("europepmc", "q", rows=[{"title": "a"}, {"title": "b", "retrieved_at": "2000-01-01T00:00:00+00:00"}])
    _stamp_retrieved_at(result, "2026-07-19T12:00:00+00:00")
    assert result.rows[0]["retrieved_at"] == "2026-07-19T12:00:00+00:00"
    # An existing (e.g. resumed) timestamp is never overwritten.
    assert result.rows[1]["retrieved_at"] == "2000-01-01T00:00:00+00:00"


def test_search_provider_stamps_retrieval_date_on_rows(monkeypatch, tmp_path):
    import nutev.search.provider_orchestrator as po

    monkeypatch.setattr(po, "search_europepmc", lambda *a, **k: [{"title": "Guideline", "doi": "10.1/x"}])
    result = search_provider(provider="europepmc", query="diet", workstream="busca1", limit=5, checkpoint_dir=tmp_path, logs_dir=tmp_path, run_id="run")
    assert result.status in {"completed", "empty"}
    assert result.rows and result.rows[0].get("retrieved_at")
    # ISO-8601 UTC (has date + time separator).
    assert "T" in result.rows[0]["retrieved_at"]
