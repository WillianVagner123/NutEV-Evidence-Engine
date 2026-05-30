from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_scoring import score_watch_item


FOOD_IS_MEDICINE_VARIANTS = {
    "produce rx",
    "fruit and vegetable prescription",
    "healthy food prescription",
    "food prescription program",
}

CULINARY_MEDICINE_PROGRAM_VARIANTS = {
    "culinary medicine curriculum",
    "culinary medicine education",
    "culinary medicine program",
    "culinary medicine training",
    "teaching kitchen curriculum",
    "teaching kitchen program",
}

DPP_LIFESTYLE_TRANSLATION_VARIANTS = {
    "intensive lifestyle intervention",
    "diabetes prevention program",
    "diabetes prevention programme",
    "national diabetes prevention program",
    "lifestyle change program",
    "lifestyle change programme",
}

FOOD_SECURITY_VARIANTS = {
    "nutrition security",
    "food security",
    "food insecurity",
    "household food insecurity",
}

FOOD_REFERRAL_DELIVERY_VARIANTS = {
    "nutrition referral",
    "food referral",
    "healthy food referral",
    "social prescribing",
    "food social prescribing",
    "food pharmacy",
    "food farmacy",
    "medical food pantry",
}


def test_lifestyle_watch_category_covers_food_is_medicine_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert FOOD_IS_MEDICINE_VARIANTS <= terms


def test_implementation_watch_category_covers_food_is_medicine_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert FOOD_IS_MEDICINE_VARIANTS <= terms


def test_lifestyle_watch_category_covers_culinary_medicine_program_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert CULINARY_MEDICINE_PROGRAM_VARIANTS <= terms


def test_food_literacy_watch_category_covers_culinary_medicine_program_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]}

    assert CULINARY_MEDICINE_PROGRAM_VARIANTS <= terms


def test_implementation_watch_category_covers_culinary_medicine_program_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert {
        "culinary medicine curriculum",
        "culinary medicine training",
        "teaching kitchen curriculum",
        "teaching kitchen program",
    } <= terms


def test_lifestyle_watch_category_covers_dpp_translation_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert DPP_LIFESTYLE_TRANSLATION_VARIANTS <= terms


def test_implementation_watch_category_covers_dpp_translation_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert DPP_LIFESTYLE_TRANSLATION_VARIANTS <= terms


def test_food_literacy_watch_category_covers_food_security_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]}

    assert FOOD_SECURITY_VARIANTS <= terms


def test_food_prescription_variants_raise_watch_priority() -> None:
    assert score_watch_item(
        {"title": "Healthy food prescription and produce rx for obesity care"}
    ) > score_watch_item({"title": "Obesity care note"})

    assert score_watch_item(
        {"title": "Fruit and vegetable prescription program for cardiometabolic risk"}
    ) > score_watch_item({"title": "Cardiometabolic risk note"})


def test_food_referral_delivery_variants_raise_watch_priority() -> None:
    baseline_score = score_watch_item({"title": "Cardiometabolic care note"})

    for term in FOOD_REFERRAL_DELIVERY_VARIANTS:
        assert score_watch_item(
            {"title": f"{term} model for cardiometabolic care"}
        ) > baseline_score


def test_dpp_translation_variants_raise_watch_priority() -> None:
    assert score_watch_item(
        {"title": "National diabetes prevention program lifestyle change program"}
    ) > score_watch_item({"title": "Type 2 diabetes prevention note"})

    assert score_watch_item(
        {"title": "Intensive lifestyle intervention for prediabetes and weight management"}
    ) > score_watch_item({"title": "Prediabetes and weight management note"})
