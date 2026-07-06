from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def test_remission_maintenance_terms_enter_busca2b_semantic_blocks() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}
    document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=4)
    }

    assert "diabetes remission implementation" in terms
    assert "weight regain prevention program" in terms
    assert "diabetes remission maintenance trial" in document_terms


def test_remission_maintenance_terms_render_in_provider_queries() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = render_queries_for_provider(keyword_taxonomy, "busca2b", "pubmed")
    query_text = "\n".join(queries).lower()

    assert "diabetes remission implementation" in query_text
    assert "weight regain prevention program" in query_text
    assert "diabetes remission maintenance trial" in query_text
