from __future__ import annotations

from nutev.export.curation import _is_prioritized


def test_curated_priority_matches_guideline_update_terms() -> None:
    row = {
        "title": "Standards of Medical Care in Diabetes 2026: clinical practice update",
        "relevance_score": 8,
        "editorial_priority_tier": "standard",
    }

    assert _is_prioritized(row) is True


def test_curated_priority_matches_food_as_medicine_implementation_terms() -> None:
    row = {
        "title": "Quality improvement study of a Produce Rx program in adults with obesity",
        "abstract": "Implementation fidelity and healthy food procurement were evaluated.",
        "relevance_score": 8,
        "editorial_priority_tier": "standard",
    }

    assert _is_prioritized(row) is True


def test_curated_priority_matches_behavior_change_implementation_terms() -> None:
    row = {
        "title": "Implementation outcomes framework for obesity care delivery",
        "abstract": "Behaviour change techniques and COM B implementation mapping were evaluated.",
        "relevance_score": 8,
        "editorial_priority_tier": "standard",
    }

    assert _is_prioritized(row) is True


def test_curated_priority_matches_steatotic_liver_terms() -> None:
    row = {
        "title": "Dietary pattern adherence in adults with MASH",
        "abstract": "A nutrition-focused cohort of metabolic dysfunction-associated steatotic liver disease.",
        "relevance_score": 8,
        "editorial_priority_tier": "standard",
    }

    assert _is_prioritized(row) is True


def test_curated_priority_still_requires_minimum_operational_score() -> None:
    row = {
        "title": "Practice guidance for healthy food procurement in primary care",
        "relevance_score": 6,
        "editorial_priority_tier": "standard",
    }

    assert _is_prioritized(row) is False


def test_curated_priority_uses_term_boundaries_for_short_terms() -> None:
    row = {
        "title": "An unrelated dashboard usability report",
        "abstract": "Operational dashboard metrics without nutrition evidence.",
        "relevance_score": 9,
        "editorial_priority_tier": "standard",
    }

    assert _is_prioritized(row) is False


def test_curated_priority_keeps_valid_dash_diet_match() -> None:
    row = {
        "title": "DASH diet adherence and blood pressure in adults",
        "abstract": "A systematic review of dietary approaches to stop hypertension.",
        "relevance_score": 9,
        "editorial_priority_tier": "standard",
    }

    assert _is_prioritized(row) is True
