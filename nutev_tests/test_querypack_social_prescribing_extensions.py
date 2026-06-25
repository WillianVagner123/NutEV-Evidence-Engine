from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import (
    WORKSTREAM_SEMANTIC_PRIORITIES,
    semantic_terms,
)
from nutev.settings import load_json


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=3)}


def test_social_prescribing_food_referral_terms_extend_semantic_blocks() -> None:
    busca1_terms = _lowered_terms("busca1")
    busca2b_terms = _lowered_terms("busca2b")
    busca1_document_terms = _lowered_terms("busca1", field="document_terms")

    assert "clinical-community food referral" in busca1_terms
    assert "food referral pathway" in busca1_terms
    assert "food resource navigation" in busca2b_terms
    assert "clinical-community food referral program" in busca1_document_terms


def test_busca1_provider_queries_include_social_prescribing_food_referral_terms() -> None:
    taxonomy = load_json("config/keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca1", "openalex")
    rendered = "\n".join(queries).lower()

    assert "clinical-community food referral" in rendered
    assert "food referral pathway" in rendered
    assert "food resource navigation" in rendered


def test_equity_access_priority_is_raised_for_food_referral_surveillance() -> None:
    priorities = WORKSTREAM_SEMANTIC_PRIORITIES["busca1"]

    assert priorities[0] == ("equity_access", 5)
