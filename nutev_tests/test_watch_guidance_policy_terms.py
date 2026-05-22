from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_quick_mode_guideline_queries_cover_policy_and_practice_recommendation_terms() -> None:
    queries = build_watch_queries(["guidelines_consensus"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "policy statement" in rendered
    assert "best practice statement" in rendered
    assert "clinical practice recommendation" in rendered
    assert "clinical practice recommendations" in rendered


def test_guideline_context_covers_policy_and_practice_recommendation_terms() -> None:
    queries = build_watch_queries(["guidelines_consensus"], since_days=30, mode="quick")
    first_query = str(queries[0]["query"]).lower()

    assert "policy statement" in first_query
    assert "best practice statement" in first_query
    assert "clinical practice recommendation" in first_query
    assert "clinical practice recommendations" in first_query


def test_policy_statement_scores_more_than_generic_note() -> None:
    assert score_watch_item(
        {"title": "Policy statement for obesity and cardiometabolic nutrition care"}
    ) > score_watch_item({"title": "Obesity and cardiometabolic nutrition care note"})


def test_best_practice_statement_scores_more_than_generic_note() -> None:
    assert score_watch_item(
        {"title": "Best practice statement for lifestyle medicine nutrition care"}
    ) > score_watch_item({"title": "Lifestyle medicine nutrition care note"})


def test_clinical_practice_recommendations_score_more_than_generic_note() -> None:
    assert score_watch_item(
        {"title": "Clinical practice recommendations for dietary management of obesity"}
    ) > score_watch_item({"title": "Dietary management of obesity note"})
