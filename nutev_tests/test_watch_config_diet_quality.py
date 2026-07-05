from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_diet_patterns_watch_terms_cover_diet_quality_indexes_and_processing() -> None:
    diet_terms = {term.lower() for term in WATCH_CATEGORIES["diet_patterns"]}

    expected_terms = {
        "diet quality",
        "diet quality index",
        "diet quality score",
        "healthy eating index",
        "alternate healthy eating index",
        "alternative healthy eating index",
        "ahei",
        "hei-2015",
        "hei 2015",
        "dietary inflammatory index",
        "empirical dietary inflammatory pattern",
        "ultra-processed food",
        "ultra processed food",
        "ultra-processed foods",
        "ultra processed foods",
        "nova classification",
        "nova food classification",
    }

    assert expected_terms <= diet_terms


def test_implementation_watch_terms_cover_diet_quality_adherence() -> None:
    implementation_terms = {
        term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]
    }

    expected_terms = {
        "dietary pattern adherence",
        "dietary adherence score",
        "diet quality adherence",
        "mediterranean diet adherence",
        "dash diet adherence",
    }

    assert expected_terms <= implementation_terms
