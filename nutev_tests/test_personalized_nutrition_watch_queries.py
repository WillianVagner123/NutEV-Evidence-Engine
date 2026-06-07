from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_personalized_nutrition_queries_are_cardiometabolic_scoped() -> None:
    queries = build_watch_queries(["personalized_nutrition"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert len(queries) == 3
    assert "personalized nutrition cardiometabolic risk" in rendered
    assert "personalised nutrition cardiometabolic risk" in rendered
    assert "precision nutrition type 2 diabetes" in rendered


def test_exhaustive_mode_personalized_nutrition_queries_cover_review_and_adherence_terms() -> None:
    queries = build_watch_queries(["personalized_nutrition"], since_days=30, mode="exhaustive")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert len(queries) == 10
    assert "personalized nutrition systematic review" in rendered
    assert "precision nutrition guideline" in rendered
    assert "tailored dietary intervention adherence" in rendered
