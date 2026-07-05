from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks.semantic_blocks import semantic_terms


def test_diet_quality_terms_extend_relevant_workstreams() -> None:
    busca2b_terms = semantic_terms("busca2b")
    a3_terms = semantic_terms("artigo3_framework")

    assert "dietary guideline adherence" in busca2b_terms
    assert "healthy eating index 2015" in busca2b_terms
    assert "diet quality index-international" in a3_terms


def test_diet_quality_document_terms_are_queryable() -> None:
    document_terms = semantic_terms("busca2b", field="document_terms")

    assert "dietary guideline adherence score" in document_terms
    assert "healthy eating index 2015 validation" in document_terms
