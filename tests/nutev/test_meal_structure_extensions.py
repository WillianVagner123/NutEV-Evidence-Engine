from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_meal_structure_terms_extend_behavioral_and_food_literacy_blocks() -> None:
    busca2b_terms = semantic_terms("busca2b", min_priority=5)
    artigo3_terms = semantic_terms("artigo3_framework", min_priority=5)

    assert "structured meal plan" in busca2b_terms
    assert "eating routine" in busca2b_terms
    assert "meal preparation routine" in artigo3_terms
    assert "family meal planning" in artigo3_terms


def test_meal_structure_document_terms_support_intervention_queries() -> None:
    busca2b_doc_terms = semantic_terms(
        "busca2b",
        field="document_terms",
        min_priority=5,
    )

    assert "structured meal planning intervention" in busca2b_doc_terms
    assert "dietary routine intervention" in busca2b_doc_terms
    assert "behavioral nutrition intervention" in busca2b_doc_terms
