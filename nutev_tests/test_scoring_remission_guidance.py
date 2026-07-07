from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_remission_guidance_supplement_prioritizes_busca2a_guidelines() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Type 2 diabetes remission consensus report for obesity nutrition care",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Type 2 diabetes report for obesity nutrition care",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_remission_guidance_supplement_prioritizes_busca2b_maintenance() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Nutrition care pathway guideline for diabetes remission maintenance and weight regain prevention",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Nutrition care pathway for diabetes and weight management",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
