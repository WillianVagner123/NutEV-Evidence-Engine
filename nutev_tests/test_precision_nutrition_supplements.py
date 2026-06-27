from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_precision_nutrition_terms_are_loaded_into_query_components() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, busca2b_components = build_structured_components(taxonomy, "busca2b")
    _, a3_components = build_structured_components(taxonomy, "a3")

    assert "precision nutrition" in busca2b_components["diet_terms"]
    assert "precision dietary intervention" in busca2b_components["nutrition_terms"]
    assert "personalized nutrition framework" in a3_components["web_hints"]


def test_precision_nutrition_bonus_gains_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Precision nutrition intervention for obesity and type 2 diabetes dietary adherence",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Dietary intervention for obesity and type 2 diabetes dietary adherence",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_personalized_nutrition_guideline_bonus_gains_busca2a_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Personalized nutrition guideline for cardiometabolic risk and type 2 diabetes",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Nutrition guideline for cardiometabolic risk and type 2 diabetes",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
