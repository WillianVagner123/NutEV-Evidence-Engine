from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_cardiorenal_terms_feed_busca2b_provider_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    _, components = build_structured_components(taxonomy, "busca2b")
    condition_terms = {term.lower() for term in components["condition_terms"]}
    provider_queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")

    assert "cardiorenal metabolic syndrome" in condition_terms
    assert "cardio-renal-metabolic syndrome" in condition_terms
    assert any("cardiorenal metabolic syndrome" in query for query in provider_queries)


def test_cardiorenal_scoring_gains_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    base_record = {
        "source": "pubmed",
        "abstract": "Adult obesity with medical nutrition therapy and implementation support.",
        "journal": "",
        "source_institution": "",
        "url": "https://example.org/cardiorenal-nutrition",
    }

    baseline = score_record(
        {
            **base_record,
            "title": "Metabolic syndrome nutrition intervention for adult obesity",
        },
        scoring_rules,
        "busca2b",
    )
    cardiorenal = score_record(
        {
            **base_record,
            "title": "Cardiorenal metabolic syndrome nutrition intervention for adult obesity",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(cardiorenal["relevance_score"]) > float(baseline["relevance_score"])
