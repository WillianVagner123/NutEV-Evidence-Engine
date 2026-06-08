from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_diet_pattern_queries_cover_diet_quality_indices() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "diet quality" in rendered
    assert "diet quality index" in rendered
    assert "healthy eating index" in rendered
    assert "alternate healthy eating index" in rendered
    assert "dietary guideline adherence" in rendered
    assert "dietary diversity score" in rendered
    assert "healthy eating pattern" in rendered
