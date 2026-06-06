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


def test_curated_priority_matches_food_access_and_social_prescribing_terms() -> None:
    row = {
        "title": "Food pharmacy referral and social prescribing in primary care",
        "abstract": "The service included grocery prescriptions and food insecurity screening.",
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
