from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=3)}


def test_carbohydrate_fiber_quality_terms_reach_guideline_and_clinical_querypacks() -> None:
    busca1_terms = _lowered_terms("busca1")
    busca2a_terms = _lowered_terms("busca2a")
    busca2b_terms = _lowered_terms("busca2b")
    busca2a_document_terms = _lowered_terms("busca2a", field="document_terms")

    assert "dietary fiber" in busca1_terms
    assert "whole grain intake" in busca1_terms
    assert "carbohydrate quality for cardiometabolic risk" in busca2a_terms
    assert "carbohydrate quality for type 2 diabetes" in busca2b_terms
    assert "low glycemic index diet" in busca2b_terms
    assert "dietary fiber guideline" in busca2a_document_terms
    assert "whole grain systematic review" in busca2a_document_terms


def test_carbohydrate_fiber_quality_terms_render_in_pubmed_queries() -> None:
    taxonomy = load_json("config/keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "carbohydrate quality for type 2 diabetes" in rendered
    assert "dietary fiber" in rendered
    assert "whole grain intervention trial" in rendered
