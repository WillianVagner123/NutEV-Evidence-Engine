from nutev.global_watch import watch_pipeline as wp
from nutev.settings import NutevSettings
from nutev.logs import setup_logger

def test_llm_enabled_without_key_does_not_break(tmp_path, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    s = NutevSettings(project_root=tmp_path, web_enabled=False)
    for d in s.output_dirs.values(): d.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(s.output_dirs['07_logs'])
    monkeypatch.setattr(wp, "search_pubmed", lambda *a, **k: [])
    monkeypatch.setattr(wp, "search_europepmc", lambda *a, **k: [])
    monkeypatch.setattr(wp, "search_openalex", lambda *a, **k: [])
    monkeypatch.setattr(wp, "search_crossref", lambda *a, **k: [])
    out = wp.run_global_watch(s, logger, since_days=7, mode='quick', resume=False, official_crawl=False, country_discovery=False, llm_enabled=True)
    assert out['rows'] > 0
