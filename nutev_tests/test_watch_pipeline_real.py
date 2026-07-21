
from nutev.global_watch import watch_pipeline as wp
from nutev.global_watch.watch_scoring import score_watch_item
from nutev.logs import setup_logger
from nutev.settings import NutevSettings


def _mk_settings(tmp_path):
    s = NutevSettings(project_root=tmp_path, web_enabled=False)
    for d in s.output_dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return s


def test_watch_normalize_hit():
    hit = wp.normalize_watch_hit({"title": "New Guideline", "url": "https://x", "doi": "10.1/abc", "year": 2026}, "pubmed", "guidelines_consensus", "q")
    assert hit["document_id"] and hit["source_provider"] == "pubmed"


def test_watch_normalize_hit_preserves_abstract_and_snippet():
    hit = wp.normalize_watch_hit(
        {
            "title": "Nutrition update",
            "abstract": "",
            "snippet": "Clinical practice guideline for obesity care",
            "url": "https://x",
            "year": 2026,
        },
        "pubmed",
        "guidelines_consensus",
        "q",
    )
    assert hit["abstract"] == ""
    assert hit["snippet"] == "Clinical practice guideline for obesity care"
    assert hit["evidence_type"] == "guideline"


def test_watch_scores_diabetes_remission_as_nutmev_priority():
    score = score_watch_item(
        {
            "title": "Type 2 diabetes remission consensus report after lifestyle intervention",
            "abstract": "Weight regain prevention and long-term weight loss maintenance in obesity care.",
            "source_provider": "pubmed",
            "category": "obesity_cardiometabolic",
            "evidence_type": "consensus",
            "is_new": True,
        }
    )
    assert score >= 90


def test_watch_pipeline_uses_real_provider_mock(tmp_path, monkeypatch):
    monkeypatch.setattr(wp, "search_pubmed", lambda q, retmax=12: [{"title": "Guideline Update", "url": "https://real.org/a", "doi": "10.1/a", "year": 2026}])
    import nutev.search.provider_orchestrator as po
    for mod in (wp, po):  # europepmc/openalex/crossref dispatch via the orchestrator (Phase 1)
        monkeypatch.setattr(mod, "search_europepmc", lambda *a, **k: [], raising=False)
        monkeypatch.setattr(mod, "search_openalex", lambda *a, **k: [], raising=False)
        monkeypatch.setattr(mod, "search_crossref", lambda *a, **k: [], raising=False)
    s = _mk_settings(tmp_path)
    out = wp.run_global_watch(s, setup_logger(s.output_dirs["07_logs"]), 7, "quick", False, False, False, False)
    assert out["rows"] > 0
    csv_path = tmp_path / "09_global_watch" / "global_watch_master.csv"
    assert "pubmed" in csv_path.read_text(encoding="utf-8")
    assert "watch_seed" not in csv_path.read_text(encoding="utf-8")


def test_watch_pipeline_no_provider_failure(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("down")
    import nutev.search.provider_orchestrator as po
    monkeypatch.setattr(wp, "search_pubmed", boom)
    for mod in (wp, po):  # europepmc/openalex/crossref dispatch via the orchestrator (Phase 1)
        monkeypatch.setattr(mod, "search_europepmc", boom, raising=False)
        monkeypatch.setattr(mod, "search_openalex", boom, raising=False)
        monkeypatch.setattr(mod, "search_crossref", boom, raising=False)
    s = _mk_settings(tmp_path)
    out = wp.run_global_watch(s, setup_logger(s.output_dirs["07_logs"]), 7, "quick", False, False, False, False)
    assert out["rows"] >= 1
    events = (tmp_path / "07_logs" / "run_events.jsonl").read_text(encoding="utf-8")
    assert "provider_failed" in events


def test_watch_digest_real_items(tmp_path):
    run_dir = tmp_path / "run"
    latest = tmp_path / "latest.md"
    wp.write_digest([
        {"title": "WHO guideline", "url": "https://who.int/x", "source_provider": "pubmed", "download_status": "metadata_only", "watch_score": 90}
    ], run_dir, latest)
    txt = latest.read_text(encoding="utf-8")
    assert "https://who.int/x" in txt


def test_since_days_in_provider_queries(tmp_path, monkeypatch):
    seen = {}
    def fake_pubmed(q, retmax=12):
        seen["q"] = q
        return []
    monkeypatch.setattr(wp, "search_pubmed", fake_pubmed)
    import nutev.search.provider_orchestrator as po
    for mod in (wp, po):  # europepmc/openalex/crossref dispatch via the orchestrator (Phase 1)
        monkeypatch.setattr(mod, "search_europepmc", lambda *a, **k: [], raising=False)
        monkeypatch.setattr(mod, "search_openalex", lambda *a, **k: [], raising=False)
        monkeypatch.setattr(mod, "search_crossref", lambda *a, **k: [], raising=False)
    sconf = _mk_settings(tmp_path)
    wp.run_global_watch(sconf, setup_logger(sconf.output_dirs["07_logs"]), 7, "quick", False, False, False, False)
    assert "Date - Publication" in seen["q"]
