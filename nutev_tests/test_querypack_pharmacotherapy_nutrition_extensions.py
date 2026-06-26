from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=5)}


def test_pharmacotherapy_nutrition_terms_reach_clinical_workstreams() -> None:
    busca2a_terms = _lowered_terms("busca2a")
    busca2b_terms = _lowered_terms("busca2b")
    busca2b_document_terms = _lowered_terms("busca2b", field="document_terms")

    assert "glp-1 receptor agonist nutrition care" in busca2a_terms
    assert "semaglutide dietary counseling" in busca2a_terms
    assert "tirzepatide lifestyle intervention" in busca2b_terms
    assert "protein intake during weight loss pharmacotherapy" in busca2b_terms
    assert "obesity pharmacotherapy nutrition care" in busca2b_document_terms


def test_pharmacotherapy_nutrition_terms_render_in_pubmed_queries() -> None:
    taxonomy = load_json("config/keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "glp-1 receptor agonist nutrition care" in rendered
    assert "semaglutide lifestyle intervention" in rendered
    assert "tirzepatide nutrition care" in rendered