from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def test_busca2b_prioritizes_preference_acceptability_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}
    document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=5)
    }

    assert "dietary preference" in terms
    assert "patient-centered nutrition" in terms
    assert "preference-sensitive nutrition" in terms
    assert "dietary intervention acceptability" in terms
    assert "culturally tailored dietary intervention" in terms
    assert "dietary intervention acceptability study" in document_terms
    assert "shared decision making nutrition intervention" in document_terms


def test_busca2b_pubmed_queries_cover_preference_acceptability_terms() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = [
        query.lower()
        for query in render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    ]

    assert any("dietary preference" in query for query in queries)
    assert any("intervention acceptability" in query for query in queries)
    assert any("shared decision making for nutrition" in query for query in queries)
