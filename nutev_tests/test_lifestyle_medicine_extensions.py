from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_lifestyle_medicine_practice_terms_extend_clinical_workstreams() -> None:
    busca2b_terms = semantic_terms("busca2b", min_priority=4)

    assert "lifestyle medicine practice" in busca2b_terms
    assert "lifestyle medicine prescription" in busca2b_terms
    assert "therapeutic lifestyle prescription" in busca2b_terms


def test_lifestyle_medicine_document_terms_extend_guidance_queries() -> None:
    busca2a_doc_terms = semantic_terms(
        "busca2a",
        field="document_terms",
        min_priority=3,
    )

    assert "lifestyle medicine practice guideline" in busca2a_doc_terms
    assert "lifestyle medicine consensus statement" in busca2a_doc_terms
    assert "lifestyle medicine competency framework" in busca2a_doc_terms
