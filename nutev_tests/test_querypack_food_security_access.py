from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def test_food_security_access_terms_feed_high_priority_semantic_blocks() -> None:
    terms = "\n".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "household food insecurity" in terms
    assert "food security screening" in terms
    assert "nutrition insecurity referral" in terms
    assert "clinical-community food referral" in terms


def test_food_security_access_terms_render_in_provider_queries(keyword_taxonomy: dict) -> None:
    queries = render_queries_for_provider(keyword_taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "household food insecurity" in rendered
    assert "food security screening" in rendered
    assert "nutrition insecurity referral" in rendered
