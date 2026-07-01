from __future__ import annotations

from pathlib import Path

from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path("config") / "keyword_taxonomy.json")


def test_social_navigation_supplement_extends_global_implementation_terms() -> None:
    taxonomy = _taxonomy()
    terms = taxonomy["global"]["implementation_behavior"]["food_navigation_referral"]

    assert "food navigation" in terms
    assert "nutrition navigation" in terms
    assert "closed-loop food referral" in terms
    assert "food benefits navigation" in terms


def test_social_navigation_supplement_extends_busca_workstreams() -> None:
    taxonomy = _taxonomy()

    busca1_terms = taxonomy["workstreams"]["busca1"]["focus_terms"]
    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]

    assert "food resource navigation" in busca1_terms
    assert "food navigation cardiometabolic trial" in busca2b_hints
    assert "closed-loop food referral trial" in busca2b_hints


def test_social_navigation_terms_extend_food_access_outcomes() -> None:
    taxonomy = _taxonomy()
    outcomes = taxonomy["outcomes"]["food_access_implementation"]

    assert "community resource navigation" in outcomes
    assert "nutrition referral pathway" in outcomes
    assert "nutrition benefits navigation" in outcomes
