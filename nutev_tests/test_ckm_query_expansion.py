from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_ckm_terms_load_into_cardiometabolic_workstream_components() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    for workstream in ("busca2a", "busca2b"):
        _, components = build_structured_components(taxonomy, workstream)
        condition_terms = {term.lower() for term in components["condition_terms"]}
        web_hints = {term.lower() for term in components["web_hints"]}

        assert "ckm syndrome" in condition_terms
        assert "cardiovascular-kidney-metabolic health" in condition_terms
        assert any("ckm" in hint for hint in web_hints)


def test_ckm_terms_reach_provider_query_rendering() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")

    assert any("ckm" in query.lower() for query in queries)
    assert any("cardiovascular-kidney-metabolic" in query.lower() for query in queries)


def test_ckm_health_terms_gain_configured_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Dietary guideline for cardiovascular-kidney-metabolic health and obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Dietary guideline for cardiometabolic health and obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
