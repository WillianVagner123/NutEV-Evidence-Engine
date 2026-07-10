from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=3)}


def test_hypertension_diet_terms_reach_cardiometabolic_workstreams() -> None:
    busca2a_terms = _lowered_terms("busca2a")
    busca2b_terms = _lowered_terms("busca2b")
    busca2a_document_terms = _lowered_terms("busca2a", field="document_terms")

    assert "dietary sodium reduction" in busca2a_terms
    assert "salt reduction" in busca2a_terms
    assert "dietary potassium" in busca2b_terms
    assert "sodium potassium ratio" in busca2b_terms
    assert "blood pressure dietary intervention" in busca2b_terms
    assert "sodium reduction guideline" in busca2a_document_terms
    assert "salt substitute trial" in busca2a_document_terms


def test_hypertension_diet_terms_render_in_provider_queries() -> None:
    taxonomy = load_json("config/keyword_taxonomy.json")

    pubmed_queries = "\n".join(render_queries_for_provider(taxonomy, "busca2a", "pubmed")).lower()
    europepmc_queries = "\n".join(render_queries_for_provider(taxonomy, "busca2b", "europepmc")).lower()

    assert "dietary sodium reduction" in pubmed_queries
    assert "sodium reduction guideline" in pubmed_queries
    assert "dietary potassium" in europepmc_queries
    assert "blood pressure dietary intervention" in europepmc_queries
