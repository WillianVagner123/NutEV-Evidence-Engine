from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_diet_pattern_queries_cover_sustainable_diet_variants() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "sustainable healthy diet" in rendered
    assert "sustainable healthy diets" in rendered
    assert "healthy sustainable diet" in rendered
    assert "healthy and sustainable diets" in rendered
    assert "sustainable dietary pattern" in rendered
