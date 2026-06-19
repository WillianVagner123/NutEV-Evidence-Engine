from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_food_literacy_queries_add_operational_literacy_and_policy_context() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=7,
        mode="quick",
    )
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "cooking skills" in rendered
    assert "meal preparation" in rendered
    assert "healthy grocery shopping" in rendered
    assert "food budgeting" in rendered
    assert "food resource management" in rendered
    assert "food label literacy" in rendered
    assert "label reading" in rendered
    assert "food policy" in rendered
    assert "nutrition policy" in rendered
