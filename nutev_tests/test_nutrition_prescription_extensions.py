from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_nutrition_prescription_terms_expand_intervention_workstreams() -> None:
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b")}
    busca2a_terms = {term.lower() for term in semantic_terms("busca2a")}

    assert "nutrition prescription" in busca2b_terms
    assert "personalized meal planning" in busca2b_terms
    assert "dietary prescription" in busca2a_terms


def test_nutrition_prescription_document_terms_support_guideline_and_intervention_retrieval() -> None:
    busca2b_document_terms = {
        term.lower() for term in semantic_terms("busca2b", field="document_terms")
    }
    artigo3_document_terms = {
        term.lower()
        for term in semantic_terms("artigo3_framework", field="document_terms")
    }

    assert "nutrition prescription guideline" in busca2b_document_terms
    assert "personalized meal planning intervention" in artigo3_document_terms
