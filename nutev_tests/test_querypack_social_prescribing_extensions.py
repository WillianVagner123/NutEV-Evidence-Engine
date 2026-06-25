from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.builders import build_workstream_queries


def test_social_prescribing_food_referral_terms_extend_semantic_blocks() -> None:
    equity_terms = {
        item.lower()
        for item in semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["equity_access"]["terms"]
    }
    implementation_terms = {
        item.lower()
        for item in semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["implementation_science"]["terms"]
    }

    assert "clinical-community food referral" in equity_terms
    assert "food referral pathway" in equity_terms
    assert "food resource navigation" in implementation_terms


def test_busca1_queries_include_social_prescribing_food_referral_terms() -> None:
    queries = build_workstream_queries("busca1", max_queries=80)
    rendered = " ".join(query.lower() for query in queries)

    assert "clinical-community food referral" in rendered
    assert "food referral pathway" in rendered


def test_equity_access_priority_is_raised_for_food_referral_surveillance() -> None:
    priorities = semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES["busca1"]

    assert priorities[0] == ("equity_access", 5)
