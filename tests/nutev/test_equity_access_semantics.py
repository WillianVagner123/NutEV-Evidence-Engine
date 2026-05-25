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


def test_busca2b_high_priority_semantic_terms_include_equity_screening_terms() -> None:
    terms = semantic_terms("busca2b", min_priority=4)

    assert "food insecurity screening" in terms
    assert "hunger vital sign" in terms
    assert "social needs screening" in terms


def test_busca2b_provider_queries_surface_equity_screening_terms() -> None:
    queries = render_queries_for_provider(_load_taxonomy(), "busca2b", "pubmed")

    assert any(
        "food insecurity screening" in query
        or "hunger vital sign" in query
        or "social needs screening" in query
        for query in queries
    )
