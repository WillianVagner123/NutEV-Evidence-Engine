from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def test_cardiometabolic_multimorbidity_terms_enter_clinical_semantic_blocks() -> None:
    busca2a_terms = {term.lower() for term in semantic_terms("busca2a", min_priority=4)}
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}
    busca2b_document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=4)
    }

    assert "cardiometabolic multimorbidity" in busca2a_terms
    assert "metabolically unhealthy obesity" in busca2b_terms
    assert "metabolic syndrome remission" in busca2b_terms
    assert "cardiometabolic multimorbidity systematic review" in busca2b_document_terms


def test_cardiometabolic_multimorbidity_terms_render_in_provider_queries() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = render_queries_for_provider(keyword_taxonomy, "busca2b", "pubmed")
    query_text = "\n".join(queries).lower()

    assert "cardiometabolic multimorbidity" in query_text
    assert "metabolically unhealthy obesity" in query_text
    assert "metabolic syndrome remission" in query_text
    assert "cardiometabolic multimorbidity systematic review" in query_text
