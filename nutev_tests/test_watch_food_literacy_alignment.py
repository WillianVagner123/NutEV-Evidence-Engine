from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_food_literacy_quick_mode_adds_environment_and_agency_terms() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=7,
        mode="quick",
    )
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "food budgeting" in rendered
    assert "food resource management" in rendered
    assert "shopping skills" in rendered
    assert "healthy grocery shopping" in rendered
    assert "food label literacy" in rendered
    assert "retail food environment" in rendered
    assert "healthy food procurement" in rendered
    assert "menu labeling" in rendered
    assert "meal routine" in rendered


def test_food_literacy_environment_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": (
                "Food budgeting, healthy grocery shopping, menu labeling, "
                "and healthy food procurement in obesity care"
            )
        }
    )
    baseline = score_watch_item({"title": "Obesity care note"})

    assert enriched > baseline
