from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=4)}


def test_sodium_potassium_terms_reach_cardiometabolic_querypacks() -> None:
    busca1_terms = _lowered_terms("busca1")
    busca2a_terms = _lowered_terms("busca2a")
    busca2b_terms = _lowered_terms("busca2b")
    busca2a_document_terms = _lowered_terms("busca2a", field="document_terms")

    assert "sodium reduction" in busca1_terms
    assert "dietary sodium" in busca2a_terms
    assert "potassium-enriched salt" in busca2a_terms
    assert "hypertension nutrition therapy" in busca2b_terms
    assert "sodium reduction guideline" in busca2a_document_terms
    assert "salt substitute trial" in busca2a_document_terms


def test_sodium_potassium_terms_render_in_pubmed_queries() -> None:
    taxonomy = load_json("config/keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "dietary sodium" in rendered
    assert "salt substitute trial" in rendered
    assert "hypertension nutrition therapy" in rendered
