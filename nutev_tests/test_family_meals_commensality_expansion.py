from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def test_family_meals_terms_enter_artigo3_commensality_blocks() -> None:
    terms = {term.lower() for term in semantic_terms("a3", min_priority=4)}
    document_terms = {
        term.lower()
        for term in semantic_terms("a3", field="document_terms", min_priority=4)
    }

    assert "family meals intervention" in terms
    assert "mealtime routine intervention" in terms
    assert "family meals systematic review" in document_terms


def test_family_meals_terms_render_in_provider_queries() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = render_queries_for_provider(keyword_taxonomy, "a3", "pubmed")
    query_text = "\n".join(queries).lower()

    assert "family meals intervention" in query_text
    assert "mealtime routine intervention" in query_text
    assert "family meals systematic review" in query_text
