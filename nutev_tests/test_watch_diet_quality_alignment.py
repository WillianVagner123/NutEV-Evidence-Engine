from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_diet_patterns_thesis_queries_include_diet_quality_terms() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=30, mode="thesis")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "healthy eating pattern" in rendered
    assert "healthy dietary pattern" in rendered
    assert "diet quality" in rendered
    assert "healthy eating index" in rendered


def test_diet_quality_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": "Diet quality and healthy eating index in cardiometabolic risk",
            "abstract": "Healthy dietary pattern adherence among adults with obesity.",
            "category": "diet_patterns",
        }
    )
    generic = score_watch_item({"title": "Diet and health overview"})

    assert enriched > generic
