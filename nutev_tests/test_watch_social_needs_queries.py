from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def _rendered_queries(category: str) -> str:
    queries = build_watch_queries([category], since_days=7, mode="quick")
    return " ".join(str(row["query"]).lower() for row in queries)


def test_lifestyle_watch_queries_cover_social_needs_food_access_terms() -> None:
    rendered = _rendered_queries("lifestyle_medicine")

    assert "food insecurity screening" in rendered
    assert "hunger vital sign" in rendered
    assert "social needs referral" in rendered
    assert "social prescribing" in rendered
    assert "community food program" in rendered


def test_implementation_watch_queries_cover_navigation_and_chw_terms() -> None:
    rendered = _rendered_queries("implementation_behavior")

    assert "community health worker" in rendered
    assert "community health worker-led nutrition" in rendered
    assert "patient navigation" in rendered
    assert "care navigation" in rendered
    assert "food bank partnership" in rendered
