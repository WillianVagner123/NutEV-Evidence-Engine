from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2b_semantic_terms_include_community_food_distribution_models() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}

    assert "mobile produce market" in terms
    assert "farm share" in terms
    assert "community food distribution" in terms
    assert "home-delivered produce" in terms


def test_busca2b_document_terms_include_community_food_access_evaluations() -> None:
    document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=4)
    }

    assert "farm share program evaluation" in document_terms
    assert "mobile produce market program evaluation" in document_terms
    assert "community food distribution program evaluation" in document_terms
