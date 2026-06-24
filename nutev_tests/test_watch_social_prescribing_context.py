from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_quick_watch_queries_include_social_prescribing_access_context() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = " ".join(str(item["query"]).lower() for item in queries)

    assert "social prescribing" in rendered
    assert "nutrition social prescribing" in rendered
    assert "screen and refer" in rendered
    assert "community resource referral" in rendered
    assert "patient navigation" in rendered


def test_social_prescribing_access_signals_improve_watch_priority() -> None:
    access_item = {
        "title": "Nutrition social prescribing and closed-loop referral for food insecurity in cardiometabolic care",
        "source_provider": "pubmed",
    }
    generic_item = {
        "title": "Cardiometabolic care note",
        "source_provider": "pubmed",
    }

    assert score_watch_item(access_item) > score_watch_item(generic_item)
