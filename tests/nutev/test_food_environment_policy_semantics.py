import json
from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _load_taxonomy() -> dict:
    return json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "keyword_taxonomy.json").read_text(
            encoding="utf-8"
        )
    )


def test_busca1_semantic_terms_include_food_environment_policy_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca1", min_priority=3)}

    assert "choice architecture intervention" in terms
    assert "healthy food procurement policy" in terms
    assert "food service guidelines" in terms


def test_busca2b_provider_queries_surface_food_environment_policy_terms() -> None:
    queries = [
        query.lower()
        for query in render_queries_for_provider(_load_taxonomy(), "busca2b", "pubmed")
    ]

    assert any(
        "choice architecture intervention" in query
        or "healthy food procurement policy" in query
        or "food service guidelines" in query
        for query in queries
    )
