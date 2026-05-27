from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _load_taxonomy() -> dict:
    return load_json("config/keyword_taxonomy.json")


def test_pubmed_focus_overflow_recovers_time_restricted_eating_with_anchors() -> None:
    taxonomy = _load_taxonomy()

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")

    matching = [query for query in queries if "time-restricted eating" in query]
    assert matching
    assert any("obesity" in query or "diabetes" in query for query in matching)
    assert any(
        "glycemic control" in query or "randomized controlled trial" in query
        for query in matching
    )


def test_openalex_focus_overflow_recovers_meal_replacement_with_anchors() -> None:
    taxonomy = _load_taxonomy()

    queries = render_queries_for_provider(taxonomy, "busca2b", "openalex")

    matching = [query for query in queries if "meal replacement" in query]
    assert matching
    assert any("obesity" in query or "diabetes" in query for query in matching)
    assert any("weight loss" in query or "guideline" in query for query in matching)
