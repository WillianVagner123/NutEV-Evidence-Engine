from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_group_care_delivery_terms_extend_busca2b_query_components() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(keyword_taxonomy, "busca2b")

    behavior_terms = {term.lower() for term in components["behavior_terms"]}

    assert "shared medical appointments" in behavior_terms
    assert "group-based nutrition intervention" in behavior_terms
    assert "group-based weight management" in behavior_terms


def test_group_care_delivery_scoring_supplement_prioritizes_nutmev_items() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Group-based nutrition intervention for dietary adherence in obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Nutrition intervention for dietary adherence in obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
