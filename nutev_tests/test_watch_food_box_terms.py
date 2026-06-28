from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def _rendered_query(category: str) -> str:
    queries = build_watch_queries([category], since_days=7, mode="quick")
    return " ".join(str(item["query"]).lower() for item in queries)


def test_quick_mode_lifestyle_queries_cover_food_box_access_variants() -> None:
    rendered = _rendered_query("lifestyle_medicine")

    assert "healthy food box" in rendered
    assert "produce box" in rendered
    assert "food box program" in rendered
    assert "community food box" in rendered


def test_quick_mode_implementation_queries_cover_food_box_access_variants() -> None:
    rendered = _rendered_query("implementation_behavior")

    assert "healthy food box" in rendered
    assert "produce box" in rendered
    assert "food box program" in rendered
    assert "community food box" in rendered


def test_quick_mode_food_literacy_queries_cover_food_box_access_variants() -> None:
    rendered = _rendered_query("food_literacy_culinary_commensality")

    assert "healthy food box" in rendered
    assert "produce box" in rendered
    assert "food box program" in rendered
    assert "community food box" in rendered
