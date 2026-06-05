from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_scoring_rule_extension_preserves_existing_rules() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))

    assert scoring_rules["keyword_points"]["guideline"] == 3
    assert scoring_rules["workstream_bonus"]["busca2b"]["mediterranean diet"] == 4
    assert scoring_rules["keyword_points"]["type 2 diabetes remission"] == 4


def test_metabolic_remission_terms_gain_busca2a_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Consensus report on type 2 diabetes remission and long-term weight loss maintenance in clinical obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Consensus report on type 2 diabetes and weight management in clinical obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_metabolic_remission_terms_gain_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Randomized trial of Mediterranean diet for glycemic remission and weight regain prevention in obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Randomized trial of Mediterranean diet for glycemic control and weight management in obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
