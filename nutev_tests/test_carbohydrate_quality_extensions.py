from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.carbohydrate_quality_extensions import (
    CARBOHYDRATE_FIBER_QUALITY_DOCUMENT_TERMS,
    CARBOHYDRATE_FIBER_QUALITY_TERMS,
    apply_carbohydrate_quality_extensions,
)


def test_carbohydrate_quality_extension_adds_cardiometabolic_terms() -> None:
    apply_carbohydrate_quality_extensions()

    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["carbohydrate_fiber_quality"]
    terms = {term.lower() for term in block["terms"]}
    document_terms = {term.lower() for term in block["document_terms"]}

    assert "postprandial glycemia" in terms
    assert "whole grain cardiometabolic risk" in terms
    assert "dietary fiber cardiometabolic risk" in terms
    assert "glycemic index cardiometabolic risk" in terms
    assert "whole grain cardiometabolic systematic review" in document_terms
    assert "dietary fiber cardiometabolic intervention trial" in document_terms


def test_carbohydrate_quality_extension_is_idempotent() -> None:
    apply_carbohydrate_quality_extensions()
    apply_carbohydrate_quality_extensions()

    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["carbohydrate_fiber_quality"]
    assert len(block["terms"]) == len({term.lower() for term in block["terms"]})
    assert len(block["document_terms"]) == len(
        {term.lower() for term in block["document_terms"]}
    )
    assert set(CARBOHYDRATE_FIBER_QUALITY_TERMS).issubset(set(block["terms"]))
    assert set(CARBOHYDRATE_FIBER_QUALITY_DOCUMENT_TERMS).issubset(
        set(block["document_terms"])
    )
