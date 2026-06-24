from __future__ import annotations

from nutev.global_watch.watch_query_builder import QUICK_MODE_SEED_GROUPS, build_watch_queries


def _flatten_seed_groups(values: list[list[str]]) -> list[str]:
    return [term for group in values for term in group]


def test_food_literacy_quick_watch_keeps_operational_literacy_anchors() -> None:
    category_terms = QUICK_MODE_SEED_GROUPS["food_literacy_culinary_commensality"]
    flattened_terms = _flatten_seed_groups(category_terms)

    assert "food label literacy" in flattened_terms
    assert "healthy grocery shopping" in flattened_terms
    assert "food access intervention" in flattened_terms
    assert "healthy food access intervention" in flattened_terms
    assert "commensality" in flattened_terms


def test_food_literacy_quick_watch_queries_include_access_and_label_terms() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=30,
        mode="quick",
    )
    query_text = "\n".join(str(item["query"]) for item in queries)

    assert queries
    assert "food label literacy" in query_text
    assert "healthy food access intervention" in query_text
    assert "retail food environment" in query_text
    assert "nutrition" in query_text
    assert "cardiometabolic" in query_text
