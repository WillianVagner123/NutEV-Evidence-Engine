from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=3)}


def test_precision_personalized_nutrition_terms_reach_clinical_querypacks() -> None:
    busca2a_terms = _lowered_terms("busca2a")
    busca2b_terms = _lowered_terms("busca2b")

    assert "personalized nutrition for cardiometabolic risk" in busca2a_terms
    assert "precision nutrition for type 2 diabetes" in busca2a_terms
    assert "tailored dietary intervention for obesity" in busca2b_terms
    assert "individualized dietary intervention for type 2 diabetes" in busca2b_terms


def test_precision_personalized_nutrition_document_terms_reach_framework_querypack() -> None:
    artigo3_document_terms = _lowered_terms("artigo3_framework", field="document_terms")

    assert "personalized nutrition framework" in artigo3_document_terms
    assert "precision nutrition intervention" in artigo3_document_terms
    assert "tailored nutrition framework" in artigo3_document_terms
