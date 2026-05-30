from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_watch_categories_cover_hypertension_nutrition_terms() -> None:
    cardiometabolic_terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}
    diet_terms = {term.lower() for term in WATCH_CATEGORIES["diet_patterns"]}
    guideline_terms = {term.lower() for term in WATCH_CATEGORIES["guidelines_consensus"]}

    assert "blood pressure control" in cardiometabolic_terms
    assert "sodium reduction" in cardiometabolic_terms
    assert "salt reduction" in cardiometabolic_terms
    assert "dash dietary pattern" in diet_terms
    assert "low sodium diet" in diet_terms
    assert "hypertension guideline" in guideline_terms
