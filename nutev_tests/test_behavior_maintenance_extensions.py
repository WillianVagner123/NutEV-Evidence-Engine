from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks.semantic_blocks import semantic_terms


def test_behavior_maintenance_terms_extend_busca2b_semantics() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b")}
    document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms")
    }

    assert "habit-based dietary intervention" in terms
    assert "dietary relapse prevention" in terms
    assert "weight regain prevention intervention" in document_terms
    assert "dietary self-regulation intervention" in document_terms


def test_behavior_maintenance_terms_support_artigo3_framework() -> None:
    terms = {term.lower() for term in semantic_terms("artigo3_framework")}

    assert "healthy eating habit formation" in terms
    assert "meal planning habit" in terms
