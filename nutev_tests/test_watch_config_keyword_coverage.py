from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_watch_categories_cover_food_literacy_instrument_terms() -> None:
    food_literacy_terms = {
        term.lower()
        for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]
    }
    framework_terms = {term.lower() for term in WATCH_CATEGORIES["frameworks_instruments"]}

    expected_terms = {
        "food literacy questionnaire",
        "nutrition literacy assessment",
        "food skills questionnaire",
        "cooking confidence scale",
        "meal planning questionnaire",
        "teaching kitchen curriculum",
        "culinary medicine curriculum",
    }

    assert expected_terms <= food_literacy_terms
    assert expected_terms <= framework_terms
