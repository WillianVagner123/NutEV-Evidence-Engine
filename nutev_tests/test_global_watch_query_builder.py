from nutev.global_watch.watch_query_builder import build_watch_queries


def test_build_watch_queries_generates_queries():
    rows = build_watch_queries(["guidelines_consensus"], 7, "quick")
    assert rows and "query_id" in rows[0]


def test_food_literacy_queries_include_nutrition_literacy_in_quick_mode():
    rows = build_watch_queries(["food_literacy_culinary_commensality"], 7, "quick")
    rendered = " ".join(str(row["query"]) for row in rows).lower()
    assert "nutrition literacy" in rendered


def test_obesity_cardiometabolic_queries_include_new_liver_and_lipid_context_terms():
    rows = build_watch_queries(["obesity_cardiometabolic"], 7, "quick")
    rendered = " ".join(str(row["query"]) for row in rows).lower()
    assert "steatotic liver disease" in rendered
    assert "metabolic dysfunction-associated steatotic liver disease" in rendered
    assert "dyslipidaemia" in rendered
    assert "insulin resistance" in rendered


def test_implementation_behavior_queries_include_behavior_change_framework_terms():
    rows = build_watch_queries(["implementation_behavior"], 7, "quick")
    rendered = " ".join(str(row["query"]) for row in rows).lower()
    assert "behavior change wheel" in rendered
    assert "theoretical domains framework" in rendered
    assert "action planning" in rendered
