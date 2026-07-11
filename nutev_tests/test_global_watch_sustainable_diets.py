from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_sustainable_healthy_diet_terms_extend_diet_pattern_queries() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=30, mode="quick")
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert "sustainable healthy diets" in rendered
    assert "healthy and sustainable diet" in rendered
    assert "sustainable dietary pattern" in rendered


def test_sustainable_healthy_diet_terms_extend_diet_pattern_category() -> None:
    terms = [str(term).lower() for term in WATCH_CATEGORIES["diet_patterns"]]

    assert "sustainable healthy diets" in terms
    assert "healthy and sustainable diets" in terms
    assert "sustainable dietary patterns" in terms


def test_sustainable_healthy_diet_scoring_stays_in_nutmev_scope() -> None:
    scoped = score_watch_item(
        {"title": "Systematic review of sustainable healthy diets"}
    )
    unscoped = score_watch_item({"title": "Systematic review of dermatology care"})

    assert scoped > unscoped
