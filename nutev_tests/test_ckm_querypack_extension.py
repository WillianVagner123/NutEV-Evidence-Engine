from __future__ import annotations

from nutev.querypacks import apply_ckm_nutrition_extensions
from nutev.querypacks.semantic_blocks import semantic_terms


def test_ckm_nutrition_terms_are_available_for_clinical_workstreams() -> None:
    apply_ckm_nutrition_extensions()

    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}
    document_terms = {
        term.lower()
        for term in semantic_terms("busca2a", field="document_terms", min_priority=5)
    }

    assert "cardiovascular-kidney-metabolic disease" in terms
    assert "ckm nutrition therapy" in terms
    assert "ckm lifestyle intervention" in terms
    assert "cardiovascular-kidney-metabolic scientific statement" in document_terms
    assert "ckm clinical practice guideline" in document_terms
