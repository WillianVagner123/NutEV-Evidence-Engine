from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_build_watch_queries_respects_category_selection_and_mode_limit() -> None:
    queries = build_watch_queries(
        ["guidelines_consensus", "implementation_behavior"],
        since_days=7,
        mode="quick",
    )

    assert len(queries) == 6
    assert {item["category"] for item in queries} == {
        "guidelines_consensus",
        "implementation_behavior",
    }


def test_build_watch_queries_adds_semantic_context_for_lifestyle_terms() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=30, mode="quick")

    first_query = str(queries[0]["query"])
    assert '"lifestyle medicine"' in first_query
    assert '"food literacy"' in first_query
    assert '"culinary medicine"' in first_query
    assert '"meal planning"' in first_query
    assert '"lifestyle counseling"' in first_query
    assert '"behavioral lifestyle intervention"' in first_query


def test_build_watch_queries_adds_cardiometabolic_liver_context() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=30, mode="quick")

    first_query = str(queries[0]["query"])
    assert '"steatotic liver disease"' in first_query
    assert '"metabolic dysfunction-associated steatotic liver disease"' in first_query
    assert '"dyslipidaemia"' in first_query
    assert '"insulin resistance"' in first_query
    assert '"weight management"' in first_query
    assert '"adiposity"' in first_query


def test_build_watch_queries_adds_implementation_and_education_context() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="quick")

    first_query = str(queries[0]["query"])
    assert '"implementation science"' in first_query
    assert '"knowledge translation"' in first_query
    assert '"dietary adherence"' in first_query
    assert '"self-efficacy"' in first_query
    assert '"implementation strategy"' in first_query
    assert '"implementation outcomes"' in first_query
    assert '"process evaluation"' in first_query
    assert '"barriers and facilitators"' in first_query
    assert '"behavior change technique"' in first_query
    assert '"behavioral weight loss"' in first_query
    assert '"goal setting"' in first_query
    assert '"social support"' in first_query
    assert '"food access"' in first_query


def test_build_watch_queries_adds_food_environment_context() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=30,
        mode="quick",
    )

    first_query = str(queries[0]["query"])
    assert '"food environment"' in first_query
    assert '"nutrition education"' in first_query
    assert '"food and nutrition literacy"' in first_query
    assert '"nutrition literacy"' in first_query
    assert '"food access"' in first_query
    assert '"shared meals"' in first_query
    assert '"family meals"' in first_query
    assert '"social eating"' in first_query
    assert '"eat together"' in first_query


def test_build_watch_queries_adds_guideline_report_context() -> None:
    queries = build_watch_queries(
        ["guidelines_consensus"],
        since_days=30,
        mode="quick",
    )

    first_query = str(queries[0]["query"])
    assert '"consensus report"' in first_query
    assert '"practice advisory"' in first_query
    assert '"expert consensus"' in first_query
    assert '"clinical guidance"' in first_query
    assert '"practice recommendation"' in first_query
    assert '"food guide"' in first_query
    assert '"nutrition guideline"' in first_query


def test_build_watch_queries_adds_diet_pattern_context_from_taxonomy() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=30, mode="quick")

    first_query = str(queries[0]["query"])
    assert '"whole-food plant-based"' in first_query
    assert '"portfolio diet"' in first_query
    assert '"nordic diet"' in first_query


def test_build_watch_queries_prioritizes_guideline_like_terms() -> None:
    guideline_queries = build_watch_queries(
        ["guidelines_consensus"],
        since_days=30,
        mode="quick",
    )
    behavior_queries = build_watch_queries(
        ["implementation_behavior"],
        since_days=30,
        mode="quick",
    )

    assert guideline_queries[0]["priority"] == 1
    assert behavior_queries[0]["priority"] == 2


def test_quick_mode_guidelines_cover_consensus_and_statement_seed_groups() -> None:
    queries = build_watch_queries(["guidelines_consensus"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "consensus statement" in rendered
    assert "scientific statement" in rendered
    assert "position statement" in rendered


def test_quick_mode_implementation_queries_cover_behavior_change_group() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "behavior change" in rendered
    assert "motivational interviewing" in rendered
    assert "social support" in rendered


def test_quick_mode_diet_pattern_queries_cover_plant_based_and_planetary_blocks() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "plant-based diet" in rendered
    assert "vegetarian diet" in rendered
    assert "vegan diet" in rendered
    assert "eat-lancet" in rendered
    assert "planetary health diet" in rendered
    assert "portfolio diet" in rendered
    assert "nordic diet" in rendered


def test_quick_mode_obesity_queries_cover_cardiometabolic_and_liver_blocks() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "cardiometabolic risk" in rendered
    assert "type 2 diabetes" in rendered
    assert "metabolic syndrome" in rendered
    assert "hypertension" in rendered
    assert "dyslipidemia" in rendered
    assert "masld" in rendered
    assert "nafld" in rendered
    assert "steatotic liver disease" in rendered


def test_quick_mode_lifestyle_queries_cover_core_intervention_and_counseling_blocks() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "lifestyle medicine nutrition" in rendered
    assert "therapeutic lifestyle changes" in rendered
    assert "lifestyle counseling" in rendered
    assert "lifestyle counselling" in rendered


def test_quick_mode_food_literacy_queries_cover_literacy_culinary_and_commensality_blocks() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=7,
        mode="quick",
    )
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "food and nutrition literacy" in rendered
    assert "culinary medicine" in rendered
    assert "cooking skills" in rendered
    assert "food environment" in rendered
    assert "commensality" in rendered
    assert "family meals" in rendered


def test_quick_mode_framework_queries_cover_framework_instrument_and_validation_blocks() -> None:
    queries = build_watch_queries(["frameworks_instruments"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "behavior change framework" in rendered
    assert "survey instrument" in rendered
    assert "food literacy instrument" in rendered
    assert "psychometric validation" in rendered
    assert "scale development" in rendered
