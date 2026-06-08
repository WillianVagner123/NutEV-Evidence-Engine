from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2a_includes_ckm_renal_nutrition_terms() -> None:
    terms = [term.lower() for term in semantic_terms("busca2a")]

    assert "cardio-kidney-metabolic syndrome" in terms
    assert "chronic kidney disease nutrition care" in terms
    assert "diabetic kidney disease nutrition" in terms


def test_busca2b_includes_ckm_renal_document_terms() -> None:
    document_terms = [
        term.lower() for term in semantic_terms("busca2b", field="document_terms")
    ]

    assert "ckm scientific statement" in document_terms
    assert "chronic kidney disease nutrition guideline" in document_terms
    assert "diabetic kidney disease nutrition consensus" in document_terms


def test_ckm_renal_extensions_are_idempotent() -> None:
    first = semantic_terms("busca2a")
    second = semantic_terms("busca2a")

    assert len(first) == len(set(term.lower() for term in first))
    assert first == second
