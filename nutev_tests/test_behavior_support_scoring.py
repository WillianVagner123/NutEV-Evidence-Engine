from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_behavior_support_supplement_prioritizes_nutrition_coaching() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Nutrition coaching with food self-monitoring for dietary adherence in obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "General coaching for adherence in obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_behavior_support_supplement_prioritizes_adherence_planning_for_framework() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Adherence planning and nutrition self-monitoring framework for food literacy",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )
    baseline = score_record(
        {
            "title": "General adherence framework for food literacy",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
