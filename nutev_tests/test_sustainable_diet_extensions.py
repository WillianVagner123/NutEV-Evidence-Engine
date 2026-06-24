from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_sustainable_healthy_diets_extend_querypack_semantics() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}

    assert "sustainable healthy diets" in terms
    assert "healthy and sustainable diets" in terms
    assert "sustainable dietary patterns" in terms


def test_sustainable_healthy_diet_document_terms_are_queryable() -> None:
    terms = {
        term.lower()
        for term in semantic_terms("busca1", field="document_terms", min_priority=4)
    }

    assert "sustainable healthy diet guideline" in terms
    assert "sustainable dietary pattern systematic review" in terms
