from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_scoring import score_watch_item


FOOD_IS_MEDICINE_VARIANTS = {
    "produce rx",
    "fruit and vegetable prescription",
    "healthy food prescription",
    "food prescription program",
}


def test_lifestyle_watch_category_covers_food_is_medicine_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert FOOD_IS_MEDICINE_VARIANTS <= terms


def test_implementation_watch_category_covers_food_is_medicine_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert FOOD_IS_MEDICINE_VARIANTS <= terms


def test_food_prescription_variants_raise_watch_priority() -> None:
    assert score_watch_item(
        {"title": "Healthy food prescription and produce rx for obesity care"}
    ) > score_watch_item({"title": "Obesity care note"})

    assert score_watch_item(
        {"title": "Fruit and vegetable prescription program for cardiometabolic risk"}
    ) > score_watch_item({"title": "Cardiometabolic risk note"})
