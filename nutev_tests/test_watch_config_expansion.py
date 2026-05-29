from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_lifestyle_watch_category_covers_nutrition_delivery_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert "nutrition care process" in terms
    assert "nutrition care pathway" in terms
    assert "nutrition care protocol" in terms
    assert "diabetes prevention program" in terms
    assert "diabetes prevention programme" in terms
    assert "dietitian-delivered intervention" in terms
    assert "dietitian-managed intervention" in terms
    assert "registered dietitian nutritionist-led intervention" in terms


def test_diet_pattern_watch_category_covers_diabetes_remission_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["diet_patterns"]}

    assert "type 2 diabetes remission" in terms
    assert "diabetes remission" in terms
    assert "remission of type 2 diabetes" in terms


def test_implementation_watch_category_covers_nutrition_care_delivery_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert "nutrition care process" in terms
    assert "nutrition care pathway" in terms
    assert "nutrition care protocol" in terms
    assert "dietitian-delivered intervention" in terms
    assert "dietitian-managed intervention" in terms
    assert "registered dietitian-led intervention" in terms
