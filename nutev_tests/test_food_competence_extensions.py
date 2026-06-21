from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_food_competence_terms_extend_article3_food_literacy_block() -> None:
    terms = " ".join(semantic_terms("artigo3_framework", min_priority=5)).lower()
    document_terms = " ".join(
        semantic_terms("artigo3_framework", field="document_terms", min_priority=5)
    ).lower()

    assert "food competence" in terms
    assert "eating competence" in terms
    assert "food preparation self-efficacy" in terms
    assert "meal planning self-efficacy" in terms
    assert "healthy grocery shopping skills" in terms
    assert "food competence questionnaire" in document_terms
    assert "eating competence inventory" in document_terms
    assert "food preparation skills questionnaire" in document_terms
    assert "cooking self-efficacy questionnaire" in document_terms


def test_food_competence_terms_support_adherence_workstream_without_lowering_priority() -> None:
    terms = " ".join(semantic_terms("busca2b", min_priority=5)).lower()
    document_terms = " ".join(
        semantic_terms("busca2b", field="document_terms", min_priority=5)
    ).lower()

    assert "food competence intervention" in terms
    assert "eating competence intervention" in terms
    assert "meal preparation confidence" in terms
    assert "food skills assessment" in document_terms
    assert "eating competence validation" in document_terms
