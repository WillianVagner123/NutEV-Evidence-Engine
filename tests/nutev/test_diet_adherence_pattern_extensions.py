from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2b_semantic_terms_include_cardiometabolic_diet_adherence() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b")}
    document_terms = {
        term.lower() for term in semantic_terms("busca2b", field="document_terms")
    }

    assert "mediterranean diet adherence" in terms
    assert "dash diet adherence" in terms
    assert "plant-based diet adherence" in terms
    assert "dietary adherence score validation" in document_terms
    assert "nutrition intervention adherence study" in document_terms


def test_busca2a_semantic_terms_include_adherence_scores_without_generic_noise() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a")}

    assert "dietary pattern adherence" in terms
    assert "diet adherence index" in terms
    assert "cardiology" not in terms
