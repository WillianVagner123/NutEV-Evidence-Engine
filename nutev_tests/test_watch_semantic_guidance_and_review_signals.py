from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_guidelines_queries_include_guidance_statement_variants() -> None:
    queries = build_watch_queries(["guidelines_consensus"], since_days=7, mode="quick")
    rendered = " ".join(str(item["query"]).lower() for item in queries)

    assert "practice guidance" in rendered
    assert "guidance statement" in rendered
    assert "joint statement" in rendered


def test_practice_guidance_scores_above_generic_guidance_note() -> None:
    assert score_watch_item({"title": "Practice guidance for obesity nutrition care"}) > score_watch_item({"title": "Obesity nutrition care note"})


def test_network_meta_analysis_scores_above_generic_pattern_note() -> None:
    assert score_watch_item({"title": "Network meta-analysis of dietary patterns for cardiometabolic risk"}) > score_watch_item({"title": "Dietary patterns for cardiometabolic risk note"})


def test_overview_of_reviews_scores_above_generic_adherence_note() -> None:
    assert score_watch_item({"title": "Overview of reviews on dietary adherence in lifestyle medicine"}) > score_watch_item({"title": "Dietary adherence in lifestyle medicine note"})
