from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_personalized_nutrition_queries_cover_adherence_and_implementation() -> None:
    queries = build_watch_queries(["personalized_nutrition"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert len(queries) == 3
    assert "personalized nutrition adherence" in rendered
    assert "personalised nutrition adherence" in rendered
    assert "precision nutrition adherence" in rendered
    assert "tailored dietary advice adherence" in rendered
    assert "individualized dietary intervention adherence" in rendered
    assert "individualised dietary intervention adherence" in rendered
    assert "personalized nutrition implementation framework" in rendered
    assert "precision nutrition implementation framework" in rendered
