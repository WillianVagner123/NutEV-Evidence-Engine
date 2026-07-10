from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_food_environment_choice_terms_extend_food_literacy_block() -> None:
    terms = {term.lower() for term in semantic_terms("artigo3_framework")}

    assert "food choice architecture" in terms
    assert "healthy default" in terms
    assert "point-of-purchase intervention" in terms


def test_food_environment_choice_document_terms_extend_busca1() -> None:
    document_terms = {
        term.lower()
        for term in semantic_terms("busca1", field="document_terms", min_priority=4)
    }

    assert "food choice architecture intervention" in document_terms
    assert "nutrition nudging intervention" in document_terms
    assert "traffic light labeling intervention" in document_terms
