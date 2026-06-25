from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks.semantic_blocks import prioritized_semantic_blocks, semantic_terms


def test_sustainable_healthy_diets_extend_lifestyle_pattern_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b")}

    assert "sustainable healthy diets" in terms
    assert "healthy and sustainable diets" in terms
    assert "eat-lancet reference diet" in terms
    assert "plant-forward dietary pattern" in terms


def test_sustainable_healthy_diets_include_guidance_and_review_document_terms() -> None:
    document_terms = {term.lower() for term in semantic_terms("busca2b", field="document_terms")}

    assert "sustainable healthy diet guideline" in document_terms
    assert "sustainable healthy diets systematic review" in document_terms
    assert "planetary health diet systematic review" in document_terms
    assert "eat-lancet reference diet systematic review" in document_terms


def test_sustainable_healthy_diets_are_prioritized_by_workstream() -> None:
    busca1_blocks = prioritized_semantic_blocks("busca1")
    busca2b_blocks = prioritized_semantic_blocks("busca2b")

    busca1_priority = next(
        block["priority"]
        for block in busca1_blocks
        if block["name"] == "sustainable_healthy_diets"
    )
    busca2b_priority = next(
        block["priority"]
        for block in busca2b_blocks
        if block["name"] == "sustainable_healthy_diets"
    )

    assert busca1_priority == 4
    assert busca2b_priority == 5
