from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_ckm_nutrition_terms_reach_cardiometabolic_workstreams() -> None:
    busca2a_terms = semantic_terms("busca2a", min_priority=5)
    busca2b_terms = semantic_terms("busca2b", min_priority=5)

    assert "ckm nutrition" in busca2a_terms
    assert "cardiovascular-kidney-metabolic dietary intervention" in busca2b_terms


def test_ckm_document_terms_reach_evidence_synthesis_queries() -> None:
    busca2a_document_terms = semantic_terms(
        "busca2a",
        field="document_terms",
        min_priority=5,
    )

    assert "ckm scientific statement" in busca2a_document_terms
    assert "cardiovascular-kidney-metabolic systematic review" in busca2a_document_terms
