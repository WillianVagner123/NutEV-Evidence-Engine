from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_social_prescribing_supplement_terms_are_loaded_into_query_taxonomy() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    terms = taxonomy["global"]["implementation_behavior"]["food_access_social_prescribing"]
    assert "social prescribing for food insecurity" in terms
    assert "social prescribing nutrition referral" in terms
    assert "closed-loop food referral" in terms

    outcome_terms = taxonomy["outcomes"]["food_access_implementation"]
    assert "link worker nutrition referral" in outcome_terms


def test_social_prescribing_food_access_terms_gain_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Social prescribing food referral with produce prescription for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Social prescribing referral for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_social_prescribing_food_access_terms_gain_busca1_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Food is medicine social prescribing and nutrition referral in dietary guidance",
            "source": "pubmed",
        },
        scoring_rules,
        "busca1",
    )
    baseline = score_record(
        {
            "title": "Social prescribing referral in dietary guidance",
            "source": "pubmed",
        },
        scoring_rules,
        "busca1",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
