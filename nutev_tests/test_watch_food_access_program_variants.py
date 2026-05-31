from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_scoring import score_watch_item


PRESCRIPTION_ACCESS_VARIANTS = {
    "nutrition prescription",
    "nutrition prescriptions",
    "grocery prescription",
    "grocery prescriptions",
    "food pharmacy",
    "fresh food pharmacy",
    "healthy food voucher",
    "healthy food vouchers",
    "grocery voucher",
    "grocery vouchers",
    "food pantry intervention",
    "food pantry interventions",
    "food bank intervention",
    "food bank interventions",
}


def test_lifestyle_category_covers_prescription_access_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert PRESCRIPTION_ACCESS_VARIANTS <= terms


def test_implementation_category_covers_prescription_access_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert PRESCRIPTION_ACCESS_VARIANTS <= terms


def test_food_literacy_category_covers_access_program_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]}

    assert {
        "healthy food voucher",
        "healthy food vouchers",
        "grocery voucher",
        "grocery vouchers",
        "food pantry intervention",
        "food pantry interventions",
        "food bank intervention",
        "food bank interventions",
    } <= terms


def test_prescription_access_variants_raise_watch_priority() -> None:
    assert score_watch_item(
        {
            "title": "Food pharmacy and grocery prescription intervention for cardiometabolic care",
        }
    ) > score_watch_item({"title": "Cardiometabolic care note"})

    assert score_watch_item(
        {
            "title": "Food pantry intervention and healthy food vouchers for dietary adherence",
        }
    ) > score_watch_item({"title": "Dietary adherence note"})
