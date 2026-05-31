from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


DPP_ACRONYM_VARIANTS = {
    "diabetes prevention program lifestyle intervention",
    "diabetes prevention programme lifestyle intervention",
    "national diabetes prevention program",
    "national diabetes prevention programme",
    "national dpp",
    "ndpp",
    "dpp lifestyle intervention",
    "dpp lifestyle change program",
}

DIABETES_REMISSION_VARIANTS = {
    "type 2 diabetes remission",
    "diabetes remission",
    "remission of type 2 diabetes",
    "type 2 diabetes reversal",
    "diabetes reversal",
    "reversal of type 2 diabetes",
    "type 2 diabetes regression",
}


def test_lifestyle_watch_category_covers_specific_dpp_acronym_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert DPP_ACRONYM_VARIANTS <= terms


def test_implementation_watch_category_covers_specific_dpp_acronym_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert DPP_ACRONYM_VARIANTS <= terms


def test_obesity_watch_category_covers_diabetes_remission_and_reversal_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    assert DIABETES_REMISSION_VARIANTS <= terms
    assert "diabetes prevention program" in terms
    assert "national diabetes prevention program" in terms
