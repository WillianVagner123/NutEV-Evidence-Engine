from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_food_access_extensions_add_community_referral_terms() -> None:
    terms = " | ".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "community-supported agriculture" in terms
    assert "csa produce box" in terms
    assert "farm share prescription" in terms
    assert "community food referral" in terms
    assert "food resource navigation" in terms


def test_food_access_extensions_add_document_level_evaluation_terms() -> None:
    document_terms = " | ".join(
        semantic_terms("busca2b", field="document_terms", min_priority=4)
    ).lower()

    assert "community-supported agriculture program evaluation" in document_terms
    assert "csa produce box program evaluation" in document_terms
    assert "farm share prescription program evaluation" in document_terms
    assert "food resource navigation program evaluation" in document_terms
