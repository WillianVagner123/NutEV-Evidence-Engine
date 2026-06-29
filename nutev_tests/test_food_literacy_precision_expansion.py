from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_food_label_comprehension_gains_busca1_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Food label comprehension and nutrition facts label use in adults with obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca1",
    )
    baseline = score_record(
        {
            "title": "Nutrition education in adults with obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca1",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_eating_competence_scale_gains_article3_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Eating competence scale and nutrition numeracy questionnaire validation",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )
    baseline = score_record(
        {
            "title": "Questionnaire validation for nutrition education",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_meal_planning_self_efficacy_gains_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Meal planning self-efficacy intervention for dietary adherence in adults with cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Dietary adherence intervention in adults with cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
