from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _rules() -> dict:
    return load_json(Path("config/scoring_rules.json"))


def test_aom_nutrition_terms_gain_busca2a_guideline_priority() -> None:
    scoring_rules = _rules()
    boosted = score_record(
        {
            "title": "Clinical practice guideline for anti-obesity medication nutrition care in adults with obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Clinical practice guideline for medication care in adults with obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_glp1_adherence_terms_gain_busca2b_intervention_priority() -> None:
    scoring_rules = _rules()
    boosted = score_record(
        {
            "title": "GLP-1 dietary adherence and nutrition intervention for weight maintenance in obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Medication adherence intervention for weight maintenance in obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_post_glp1_weight_maintenance_terms_gain_busca2b_priority() -> None:
    scoring_rules = _rules()
    boosted = score_record(
        {
            "title": "Post-GLP-1 weight maintenance with dietary adherence support after obesity treatment",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Weight maintenance support after obesity treatment",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
