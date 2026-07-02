from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_social_prescribing_nutrition_terms_extend_implementation_blocks() -> None:
    terms = semantic_terms("busca2b", min_priority=5)

    assert "social prescribing for nutrition" in terms
    assert "social prescribing for cardiometabolic risk" in terms
    assert "social prescribing dietitian referral" in terms


def test_social_prescribing_nutrition_document_terms_extend_busca1_access_blocks() -> None:
    document_terms = semantic_terms("busca1", field="document_terms", min_priority=5)

    assert "social prescribing nutrition intervention" in document_terms
    assert "social prescribing food access program evaluation" in document_terms
    assert "social prescribing food insecurity intervention" in document_terms
