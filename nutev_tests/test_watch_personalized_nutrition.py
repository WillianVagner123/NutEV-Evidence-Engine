from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


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
