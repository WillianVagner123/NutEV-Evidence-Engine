from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_diabetes_remission_category_builds_contextual_queries() -> None:
    queries = build_watch_queries(
        ["diabetes_remission_nutrition"],
        since_days=30,
        mode="quick",
    )
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert len(queries) == 3
    assert '"type 2 diabetes remission"' in rendered
    assert '"diabetes remission"' in rendered
    assert '"glycemic remission"' in rendered
    assert '"nutrition"' in rendered
    assert '"cardiometabolic"' in rendered


def test_diabetes_remission_nutrition_signals_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Type 2 diabetes remission with total diet replacement and medical nutrition therapy",
        }
    ) > score_watch_item({"title": "Type 2 diabetes nutrition note"})
