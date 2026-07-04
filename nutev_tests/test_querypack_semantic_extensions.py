from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=3)}


def test_precision_personalized_nutrition_terms_reach_clinical_querypacks() -> None:
    busca2a_terms = _lowered_terms("busca2a")
    busca2b_terms = _lowered_terms("busca2b")

    assert "personalized nutrition for cardiometabolic risk" in busca2a_terms
    assert "precision nutrition for type 2 diabetes" in busca2a_terms
    assert "tailored dietary intervention for obesity" in busca2b_terms
    assert "individualized dietary intervention for type 2 diabetes" in busca2b_terms


def test_precision_personalized_nutrition_document_terms_reach_framework_querypack() -> None:
    artigo3_document_terms = _lowered_terms("artigo3_framework", field="document_terms")

    assert "personalized nutrition framework" in artigo3_document_terms
    assert "precision nutrition intervention" in artigo3_document_terms
    assert "tailored nutrition framework" in artigo3_document_terms


def test_masld_nutrition_terms_reach_clinical_querypacks() -> None:
    busca2a_terms = _lowered_terms("busca2a")
    busca2b_terms = _lowered_terms("busca2b")
    busca2a_document_terms = _lowered_terms("busca2a", field="document_terms")
    busca2b_document_terms = _lowered_terms("busca2b", field="document_terms")

    assert "masld nutrition therapy" in busca2a_terms
    assert "mash dietary intervention" in busca2b_terms
    assert "steatotic liver disease lifestyle intervention" in busca2b_terms
    assert "masld clinical practice guideline" in busca2a_document_terms
    assert "mash lifestyle intervention trial" in busca2b_document_terms


def test_ckm_terms_reach_clinical_querypacks() -> None:
    busca2a_terms = _lowered_terms("busca2a")
    busca2b_terms = _lowered_terms("busca2b")
    busca2a_document_terms = _lowered_terms("busca2a", field="document_terms")

    assert "cardio-kidney-metabolic syndrome" in busca2a_terms
    assert "cardio kidney metabolic nutrition" in busca2b_terms
    assert "cardiorenal metabolic risk" in busca2a_terms
    assert "ckm nutrition" in busca2b_terms
    assert "cardio-kidney-metabolic scientific statement" in busca2a_document_terms


def test_food_and_eating_competence_terms_reach_framework_querypack() -> None:
    artigo3_terms = _lowered_terms("artigo3_framework")
    artigo3_document_terms = _lowered_terms("artigo3_framework", field="document_terms")

    assert "food competence" in artigo3_terms
    assert "eating competence" in artigo3_terms
    assert "satter eating competence" in artigo3_terms
    assert "eating competence scale" in artigo3_document_terms
    assert "satter eating competence inventory" in artigo3_document_terms


def test_food_and_eating_competence_terms_reach_adherence_querypacks() -> None:
    busca2b_terms = _lowered_terms("busca2b")
    busca2b_document_terms = _lowered_terms("busca2b", field="document_terms")

    assert "food competence intervention" in busca2b_terms
    assert "eating competence intervention" in busca2b_terms
    assert "eating competence questionnaire" in busca2b_document_terms
