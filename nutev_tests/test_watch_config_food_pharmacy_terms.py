from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_lifestyle_and_implementation_watch_categories_include_food_pharmacy_terms() -> None:
    lifestyle_terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}
    implementation_terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    expected_terms = {
        "food pharmacy",
        "food pharmacy program",
        "food farmacy",
        "food farmacy program",
        "medically tailored nutrition",
        "medically tailored food",
        "medically tailored food package",
        "medically tailored food packages",
    }

    assert expected_terms <= lifestyle_terms
    assert expected_terms <= implementation_terms
