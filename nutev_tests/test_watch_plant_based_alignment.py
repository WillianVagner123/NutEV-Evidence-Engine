from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_diet_pattern_queries_include_vegetarian_and_vegan_variants() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=30, mode="quick")
    rendered = "\n".join(str(query["query"]) for query in queries).lower()

    assert '"vegetarian dietary pattern"' in rendered
    assert '"vegan dietary pattern"' in rendered
    assert '"healthy plant-based diet"' in rendered
    assert '"provegetarian dietary pattern"' in rendered


def test_vegetarian_and_vegan_pattern_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": (
                "Vegetarian dietary pattern and vegan diet for obesity and "
                "cardiometabolic risk"
            )
        }
    )
    generic = score_watch_item(
        {"title": "Diet pattern for obesity and cardiometabolic risk"}
    )

    assert enriched > generic
