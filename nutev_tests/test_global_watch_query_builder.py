from nutev.global_watch.watch_query_builder import build_watch_queries


def test_build_watch_queries_generates_queries():
    rows = build_watch_queries(["guidelines_consensus"], 7, "quick")
    assert rows and "query_id" in rows[0]


def test_food_literacy_queries_include_nutrition_literacy_in_quick_mode():
    rows = build_watch_queries(["food_literacy_culinary_commensality"], 7, "quick")
    rendered = " ".join(str(row["query"]) for row in rows).lower()
    assert "nutrition literacy" in rendered
