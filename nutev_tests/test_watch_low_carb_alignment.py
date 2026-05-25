from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_quick_mode_diet_pattern_queries_cover_long_form_low_carb_variants() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "low-carb diet" in rendered
    assert "low-carbohydrate diet" in rendered
    assert "low carbohydrate diet" in rendered
    assert "very low carbohydrate diet" in rendered
    assert "very-low-carbohydrate diet" in rendered
    assert "carbohydrate-restricted diet" in rendered
    assert "carbohydrate restricted diet" in rendered
    assert "ketogenic diet" in rendered


def test_exhaustive_mode_diet_pattern_queries_cover_long_form_low_carb_variants() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=7, mode="exhaustive")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "low-carb diet" in rendered
    assert "low-carbohydrate diet" in rendered
    assert "low carbohydrate diet" in rendered
    assert "carbohydrate-restricted diet" in rendered
    assert "ketogenic diet" in rendered


def test_long_form_low_carb_signal_improves_priority() -> None:
    assert score_watch_item(
        {
            "title": "Low-carbohydrate diet and carbohydrate-restricted diet for type 2 diabetes",
        }
    ) > score_watch_item({"title": "Type 2 diabetes diet note"})
