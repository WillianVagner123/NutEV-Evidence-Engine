from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import keep_candidate_for_download, score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "config"


def test_digital_nutrition_terms_enter_busca2b_provider_queries() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "digital nutrition intervention" in rendered
    assert "remote nutrition coaching" in rendered
    assert "telehealth nutrition counseling" in rendered
    assert "dietary self-monitoring app" in rendered


def test_digital_nutrition_terms_raise_busca2b_download_priority() -> None:
    scoring_rules = load_json(CONFIG_ROOT / "scoring_rules.json")
    record = {
        "source": "pubmed",
        "title": "Digital nutrition intervention with remote nutrition coaching for adults with obesity",
        "abstract": (
            "Randomized trial of app-based dietary intervention, dietary self-monitoring app, "
            "and automated dietary feedback for type 2 diabetes remission and dietary adherence."
        ),
        "url": "https://pubmed.ncbi.nlm.nih.gov/example",
    }

    scored = score_record(record, scoring_rules, "busca2b")

    assert scored["relevance_score"] >= 20
    assert keep_candidate_for_download(scored, "busca2b")
