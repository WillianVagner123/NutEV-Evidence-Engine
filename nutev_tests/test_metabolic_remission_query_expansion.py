from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _taxonomy() -> dict:
    return load_json(PROJECT_ROOT / "config" / "keyword_taxonomy.json")


def _scoring_rules() -> dict:
    return load_json(PROJECT_ROOT / "config" / "scoring_rules.json")


def test_busca2a_metabolic_remission_terms_are_query_components() -> None:
    _, components = build_structured_components(_taxonomy(), "busca2a")

    assert "type 2 diabetes remission" in components["focus_terms"]
    assert "weight regain prevention" in components["priority_outcomes"]
    assert "diabetes remission consensus" in components["web_hints"]
    assert "remission guideline" in components["doc_type_terms"]


def test_busca2b_metabolic_remission_terms_are_query_components() -> None:
    _, components = build_structured_components(_taxonomy(), "busca2b")

    assert "diabetes remission" in components["focus_terms"]
    assert "long-term weight loss maintenance" in components["priority_outcomes"]
    assert "weight loss maintenance systematic review" in components["web_hints"]
    assert "weight loss maintenance trial" in components["doc_type_terms"]


def test_metabolic_remission_terms_gain_busca2b_scoring_priority() -> None:
    scoring_rules = _scoring_rules()
    boosted = score_record(
        {
            "title": "Diet-induced type 2 diabetes remission and weight regain prevention after lifestyle intervention",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Lifestyle intervention for diabetes and weight management",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
