from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_queries
from nutev.settings import load_json


def test_keyword_taxonomy_loads_food_care_supplement_terms() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    culinary_terms = taxonomy["global"]["nutrition_domains"]["culinary_labeling"]
    contextual_terms = taxonomy["global"]["implementation_behavior"]["contextual"]

    assert "nutrition prescription program" in culinary_terms
    assert "medically tailored nutrition" in culinary_terms
    assert "food care program" in contextual_terms


def test_busca2b_queries_include_food_care_variants() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = build_queries(taxonomy, "busca2b")
    query_blob = "\n".join(queries).lower()

    assert "nutrition prescription" in query_blob
    assert "grocery prescription" in query_blob
    assert "medically tailored nutrition" in query_blob


def test_food_care_variants_gain_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Medically tailored nutrition and grocery prescription trial for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Community nutrition support trial for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
