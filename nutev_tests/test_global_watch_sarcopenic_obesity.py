from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries


def test_sarcopenic_obesity_terms_extend_obesity_category() -> None:
    category_terms = WATCH_CATEGORIES["obesity_cardiometabolic"]

    assert "sarcopenic obesity nutrition" in category_terms
    assert "lean mass preservation weight loss" in category_terms
    assert "protein intake glp-1 receptor agonist" in category_terms


def test_sarcopenic_obesity_quick_watch_query_is_generated() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=30, mode="quick")
    query_text = "\n".join(str(item["query"]) for item in queries)

    assert queries
    assert "sarcopenic obesity nutrition" in query_text
    assert "lean mass preservation weight loss" in query_text
    assert "protein intake glp-1 receptor agonist" in query_text
    assert "obesity" in query_text or "cardiometabolic" in query_text
