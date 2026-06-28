from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_sustainable_diet_terms_extend_lifestyle_nutrition_workstreams() -> None:
    busca1_terms = {term.lower() for term in semantic_terms("busca1")}
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b")}

    assert "sustainable healthy diets" in busca1_terms
    assert "healthy and sustainable diets" in busca1_terms
    assert "sustainable dietary patterns" in busca2b_terms
    assert "plant-forward diet" in busca2b_terms


def test_sustainable_diet_document_terms_extend_guidance_and_review_queries() -> None:
    document_terms = {
        term.lower()
        for term in semantic_terms(
            "busca1",
            field="document_terms",
            min_priority=4,
        )
    }

    assert "sustainable healthy diets guideline" in document_terms
    assert "sustainable dietary patterns systematic review" in document_terms
    assert "planetary health diet systematic review" in document_terms
