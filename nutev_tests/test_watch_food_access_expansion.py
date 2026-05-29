from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


FOOD_ACCESS_PRESCRIPTION_TERMS = {
    "food pharmacy",
    "food pharmacies",
    "healthy food benefit",
    "healthy food benefits",
    "nutrition security intervention",
}


def test_lifestyle_watch_category_covers_food_access_prescription_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert FOOD_ACCESS_PRESCRIPTION_TERMS <= terms


def test_implementation_watch_category_covers_food_access_prescription_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert FOOD_ACCESS_PRESCRIPTION_TERMS <= terms


def test_food_literacy_watch_category_covers_food_access_prescription_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]}

    assert FOOD_ACCESS_PRESCRIPTION_TERMS <= terms
