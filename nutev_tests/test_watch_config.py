from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_watch_categories_include_nutrition_prescription_terms() -> None:
    expected_terms = {
        "nutrition prescription",
        "dietary prescription",
        "food prescription",
        "personalized meal planning",
        "individualized meal plan",
    }

    for category in (
        "lifestyle_medicine",
        "diet_patterns",
        "implementation_behavior",
    ):
        terms = {term.lower() for term in WATCH_CATEGORIES[category]}
        assert expected_terms & terms


def test_watch_categories_include_lifestyle_care_model_terms() -> None:
    expected_terms = {
        "whole-person care",
        "lifestyle medicine referral",
        "lifestyle prescription",
        "shared medical appointment",
        "group medical visit",
    }

    for category in ("lifestyle_medicine", "implementation_behavior"):
        terms = {term.lower() for term in WATCH_CATEGORIES[category]}
        assert expected_terms & terms
