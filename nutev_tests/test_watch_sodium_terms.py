from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_scoring import score_watch_item


def test_watch_categories_include_sodium_cardiometabolic_terms() -> None:
    cardiometabolic_terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}
    diet_pattern_terms = {term.lower() for term in WATCH_CATEGORIES["diet_patterns"]}

    assert "dietary sodium" in cardiometabolic_terms
    assert "sodium reduction" in cardiometabolic_terms
    assert "salt reduction" in cardiometabolic_terms
    assert "low sodium diet" in diet_pattern_terms
    assert "sodium-restricted diet" in diet_pattern_terms


def test_sodium_reduction_signal_improves_cardiometabolic_priority() -> None:
    assert score_watch_item(
        {
            "title": "Sodium reduction and low sodium diet for hypertension care",
        }
    ) > score_watch_item({"title": "Hypertension care note"})
