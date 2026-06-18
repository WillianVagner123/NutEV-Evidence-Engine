from __future__ import annotations

from nutev.querypacks.delivery_models import (
    group_delivery_document_terms,
    group_delivery_terms,
    nutrition_anchored_group_delivery_terms,
)


def test_group_delivery_terms_cover_shared_and_group_models() -> None:
    terms = {term.lower() for term in group_delivery_terms()}

    assert "shared medical appointments" in terms
    assert "group medical visits" in terms
    assert "group-based lifestyle intervention" in terms
    assert "group nutrition counseling" in terms


def test_group_delivery_terms_are_unique_case_insensitive() -> None:
    terms = group_delivery_terms()

    assert len(terms) == len({term.lower() for term in terms})


def test_group_delivery_document_terms_prioritize_trial_and_implementation() -> None:
    terms = {term.lower() for term in group_delivery_document_terms()}

    assert "group medical visit trial" in terms
    assert "shared medical appointment implementation" in terms


def test_group_delivery_terms_keep_nutrition_anchors() -> None:
    terms = {term.lower() for term in nutrition_anchored_group_delivery_terms()}

    assert "medical nutrition therapy" in terms
    assert "cardiometabolic risk" in terms
