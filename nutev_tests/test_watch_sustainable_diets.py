from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_thesis_mode_diet_patterns_include_sustainable_diet_terms() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=30, mode="thesis")
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert '"sustainable healthy diet"' in rendered
    assert '"healthy sustainable diets"' in rendered
    assert '"healthy and sustainable diet"' in rendered
    assert '"sustainable dietary patterns"' in rendered
    assert '"sustainable diets"' in rendered
    assert '"cardiometabolic"' in rendered
    assert '"obesity"' in rendered
