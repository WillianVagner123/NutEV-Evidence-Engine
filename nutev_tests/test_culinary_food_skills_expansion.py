from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_artigo3_semantic_terms_include_culinary_food_skills_programs() -> None:
    terms = "\n".join(semantic_terms("artigo3_framework", min_priority=4)).lower()

    assert "culinary medicine curriculum" in terms
    assert "teaching kitchen program" in terms
    assert "kitchen-based intervention" in terms
    assert "food resource management intervention" in terms


def test_busca1_semantic_terms_include_food_literacy_intervention_variants() -> None:
    terms = "\n".join(semantic_terms("busca1", min_priority=4)).lower()

    assert "culinary nutrition education" in terms
    assert "meal planning intervention" in terms
    assert "grocery shopping intervention" in terms
    assert "food label reading" in terms


def test_busca2b_document_terms_include_culinary_food_skills_anchors() -> None:
    document_terms = "\n".join(
        semantic_terms("busca2b", field="document_terms", min_priority=4)
    ).lower()

    assert "culinary medicine curriculum" in document_terms
    assert "cooking skills intervention" in document_terms
    assert "food skills intervention" in document_terms
    assert "food resource management intervention" in document_terms
