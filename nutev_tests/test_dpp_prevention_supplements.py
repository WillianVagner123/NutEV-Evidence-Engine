from __future__ import annotations

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import default_config_root, load_json


def test_dpp_supplement_feeds_busca2b_provider_queries() -> None:
    taxonomy = load_json(default_config_root() / "keyword_taxonomy.json")

    queries = "\n".join(
        render_queries_for_provider(taxonomy, "busca2b", "europepmc")
    ).lower()

    assert "diabetes prevention program" in queries
    assert "dpp lifestyle intervention" in queries
    assert "prediabetes lifestyle intervention" in queries


def test_dpp_supplement_improves_busca2b_priority_score() -> None:
    scoring = load_json(default_config_root() / "scoring_rules.json")
    dpp_record = {
        "source": "pubmed",
        "title": "Diabetes Prevention Program lifestyle intervention trial for adults with prediabetes and obesity",
        "abstract": "Dietary adherence and weight loss maintenance in a DPP lifestyle intervention for type 2 diabetes prevention.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/example",
    }
    baseline_record = {
        "source": "pubmed",
        "title": "Lifestyle intervention trial for adults with prediabetes and obesity",
        "abstract": "Dietary adherence and weight loss maintenance for type 2 diabetes prevention.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/example",
    }

    dpp_score = score_record(dict(dpp_record), scoring, "busca2b")["relevance_score"]
    baseline_score = score_record(dict(baseline_record), scoring, "busca2b")["relevance_score"]

    assert dpp_score > baseline_score
