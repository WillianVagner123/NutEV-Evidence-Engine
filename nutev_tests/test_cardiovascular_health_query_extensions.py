from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2a_semantic_terms_include_cardiovascular_health_guidance() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=4)}
    document_terms = {
        term.lower()
        for term in semantic_terms("busca2a", field="document_terms", min_priority=4)
    }

    assert "life's essential 8" in terms
    assert "cardiovascular health dietary pattern" in terms
    assert "cardiovascular health scientific statement" in document_terms
    assert "heart healthy diet guideline" in document_terms


def test_busca2b_semantic_terms_include_cardiovascular_health_nutrition() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}

    assert "cardiovascular health nutrition" in terms
    assert "dietary guidance for cardiovascular health" in terms
