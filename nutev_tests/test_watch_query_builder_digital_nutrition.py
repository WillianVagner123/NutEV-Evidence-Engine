from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_implementation_queries_cover_digital_nutrition_delivery_terms() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "digital nutrition intervention" in rendered
    assert "app-based dietary intervention" in rendered
    assert "mobile app nutrition intervention" in rendered
    assert "text messaging dietary intervention" in rendered
    assert "remote lifestyle coaching" in rendered
    assert "virtual nutrition counseling" in rendered
    assert "telehealth nutrition counseling" in rendered
    assert "digital weight management" in rendered
