from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_diet_patterns_include_ultra_processed_and_nova_terms() -> None:
    diet_terms = {term.lower() for term in WATCH_CATEGORIES["diet_patterns"]}

    assert "ultra-processed food" in diet_terms
    assert "ultra processed foods" in diet_terms
    assert "nova classification" in diet_terms
    assert "nova food classification" in diet_terms


def test_food_literacy_category_includes_environment_and_security_terms() -> None:
    food_literacy_terms = {
        term.lower()
        for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]
    }

    assert "nutrition security" in food_literacy_terms
    assert "food insecurity" in food_literacy_terms
    assert "retail food environment" in food_literacy_terms
    assert "healthy food procurement" in food_literacy_terms
    assert "menu labeling" in food_literacy_terms
    assert "menu labelling" in food_literacy_terms
