from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_implementation_watch_queries_include_behavior_change_framework_terms_in_quick_mode() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "behavior change wheel" in rendered
    assert "com-b" in rendered
    assert "intervention mapping" in rendered
    assert "implementation mapping" in rendered


def test_implementation_watch_scoring_rewards_behavior_change_framework_signals() -> None:
    plain_score = score_watch_item(
        {
            "title": "Implementation study of dietary adherence in obesity care",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    enriched_score = score_watch_item(
        {
            "title": "Behavior Change Wheel and COM-B guided intervention mapping for dietary adherence in obesity care",
            "abstract": "The implementation strategy used intervention mapping and an implementation outcomes framework to improve adherence.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 45
