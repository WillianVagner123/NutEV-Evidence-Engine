from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_personalized_nutrition_watch_queries_include_cardiometabolic_anchors() -> None:
    queries = build_watch_queries(["personalized_nutrition"], since_days=7, mode="quick")
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert '"personalized nutrition obesity"' in rendered
    assert '"precision nutrition type 2 diabetes"' in rendered
    assert '"tailored dietary advice cardiometabolic risk"' in rendered
    assert '"individualized dietary intervention type 2 diabetes"' in rendered
    assert '"nutrition"' in rendered
    assert '"obesity"' in rendered
    assert '"cardiometabolic"' in rendered


def test_personalized_nutrition_watch_queries_cover_adaptive_digital_terms() -> None:
    queries = build_watch_queries(["personalized_nutrition"], since_days=7, mode="quick")
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert "adaptive dietary intervention obesity" in rendered
    assert "adaptive nutrition intervention type 2 diabetes" in rendered
    assert "digital dietary self-monitoring cardiometabolic risk" in rendered
    assert "just-in-time adaptive intervention nutrition" in rendered


def test_personalized_nutrition_scoring_keeps_cardiometabolic_scope() -> None:
    expanded_item = {
        "title": "Adaptive dietary intervention with digital dietary self-monitoring for cardiometabolic risk",
        "category": "personalized_nutrition",
        "source_provider": "pubmed",
    }
    generic_item = {
        "title": "Personalized wellness technology note",
        "category": "personalized_nutrition",
        "source_provider": "pubmed",
    }

    assert score_watch_item(expanded_item) > score_watch_item(generic_item)
