from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_busca2b_behavior_change_planning_terms_enter_structured_components() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(keyword_taxonomy, "busca2b")
    joined_focus = " ".join(components["focus_terms"]).lower()
    joined_hints = " ".join(components["web_hints"]).lower()

    assert "action planning" in joined_focus
    assert "readiness to change" in joined_hints
    assert "transtheoretical model" in joined_hints


def test_artigo3_behavior_change_model_terms_enter_structured_components() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(keyword_taxonomy, "artigo3_framework")
    joined_focus = " ".join(components["focus_terms"]).lower()

    assert "self-regulation" in joined_focus
    assert "stages of change" in joined_focus
    assert "transtheoretical model" in joined_focus


def test_behavior_change_planning_terms_gain_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Randomized trial of action planning and readiness to change for dietary adherence in obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Randomized trial of dietary adherence in obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_behavior_change_model_terms_gain_artigo3_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Questionnaire validation using the transtheoretical model and self-regulation for nutrition literacy",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )
    baseline = score_record(
        {
            "title": "Questionnaire validation for nutrition literacy",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
