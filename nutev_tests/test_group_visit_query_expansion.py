from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def test_group_visit_terms_enter_busca2b_semantic_blocks() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}
    document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=4)
    }

    assert "shared medical appointment nutrition" in terms
    assert "group medical visit diabetes" in terms
    assert "group-based nutrition intervention trial" in document_terms


def test_group_visit_terms_render_in_provider_queries() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = render_queries_for_provider(keyword_taxonomy, "busca2b", "pubmed")
    query_text = "\n".join(queries).lower()

    assert "shared medical appointment nutrition" in query_text
    assert "group medical visit diabetes" in query_text
    assert "group-based nutrition intervention trial" in query_text
