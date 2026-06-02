from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_food_medicine_program_terms_are_queryable() -> None:
    lifestyle_terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}
    implementation_terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    expected_terms = {
        "food pharmacy",
        "nutrition prescription",
        "nutrition prescriptions",
    }

    assert expected_terms <= lifestyle_terms
    assert expected_terms <= implementation_terms
