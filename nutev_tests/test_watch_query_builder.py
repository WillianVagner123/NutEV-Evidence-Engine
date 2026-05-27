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
    assert '"hyperlipidemia"' in first_query
    assert '"hypercholesterolemia"' in first_query
    assert '"insulin resistance"' in first_query
    assert '"weight management"' in first_query
    assert '"adiposity"' in first_query


def test_build_watch_queries_adds_implementation_and_education_context() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="quick")

    first_query = str(queries[0]["query"])
    assert '"implementation science"' in first_query
    assert '"implementation research"' in first_query
    assert '"knowledge translation"' in first_query
    assert '"dietary adherence"' in first_query
    assert '"self-efficacy"' in first_query
    assert '"implementation strategy"' in first_query
    assert '"implementation outcomes"' in first_query
    assert '"implementation fidelity"' in first_query
    assert '"implementation facilitation"' in first_query
    assert '"implementation support"' in first_query
    assert '"process evaluation"' in first_query
    assert '"barriers and facilitators"' in first_query
    assert '"behavior change technique"' in first_query
    assert '"behavioral weight loss"' in first_query
    assert '"goal setting"' in first_query
    assert '"social support"' in first_query
    assert '"food access"' in first_query
    assert '"sustainability"' in first_query
    assert '"dissemination"' in first_query
    assert '"scale-up"' in first_query


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
    assert '"consensus guidance"' in first_query
    assert '"practice advisory"' in first_query
    assert '"scientific advisory"' in first_query
    assert '"best practice advice"' in first_query
    assert '"expert consensus"' in first_query
    assert '"clinical guidance"' in first_query
    assert '"practice recommendation"' in first_query
    assert '"food guide"' in first_query
    assert '"nutrition guideline"' in first_query
    assert '"joint guideline"' in first_query
    assert '"clinical decision pathway"' in first_query
    assert '"decision pathway"' in first_query
    assert '"living guideline"' in first_query


def test_build_watch_queries_adds_diet_pattern_context_from_taxonomy() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=30, mode="quick")

    first_query = str(queries[0]["query"])
    assert '"whole-food plant-based"' in first_query
    assert '"portfolio diet"' in first_query
    assert '"nordic diet"' in first_query
    assert '"ultra-processed food"' in first_query
    assert '"nova classification"' in first_query


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
    assert "consensus guidance" in rendered
    assert "scientific statement" in rendered
    assert "scientific advisory" in rendered
    assert "best practice advice" in rendered
    assert "position statement" in rendered


def test_quick_mode_implementation_queries_cover_behavior_change_group() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "behavior change" in rendered
    assert "motivational interviewing" in rendered
    assert "social support" in rendered
    assert "implementation research" in rendered
    assert "implementation fidelity" in rendered
    assert "sustainability" in rendered
    assert "dissemination" in rendered
    assert "scale-up" in rendered


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
    assert "ultra-processed food" in rendered
    assert "nova classification" in rendered


def test_quick_mode_obesity_queries_cover_cardiometabolic_and_liver_blocks() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "cardiometabolic risk" in rendered
    assert "type 2 diabetes" in rendered
    assert "metabolic syndrome" in rendered
    assert "hypertension" in rendered
    assert "dyslipidemia" in rendered
    assert "hyperlipidemia" in rendered
    assert "hypercholesterolemia" in rendered
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


def test_quick_mode_lifestyle_queries_cover_nutrition_care_terms() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "medical nutrition therapy" in rendered
    assert "nutrition counseling" in rendered
    assert "nutrition counselling" in rendered
    assert "nutrition care" in rendered


def test_quick_mode_lifestyle_queries_cover_food_access_program_variants() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "healthy food incentive" in rendered
    assert "produce voucher" in rendered
    assert "nutrition incentive" in rendered
    assert "medically tailored pantry" in rendered
    assert "medically tailored food package" in rendered
    assert "fruit and vegetable vouchers" in rendered


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


def _category_query(category: str) -> str:
    queries = build_watch_queries([category], since_days=7, mode="quick")
    assert queries
    return " ".join(item["query"] for item in queries)


def test_guidelines_context_has_food_based_guidance_variants() -> None:
    query = _category_query("guidelines_consensus")
    assert "food based dietary guideline" in query
    assert "dietary guidance" in query


def test_obesity_context_has_prediabetes_and_old_masld_name() -> None:
    query = _category_query("obesity_cardiometabolic")
    assert "prediabetes" in query
    assert "hyperlipidemia" in query
    assert "hypercholesterolemia" in query
    assert "metabolic dysfunction-associated fatty liver disease" in query


def test_implementation_quick_mode_adds_behavioral_precision_terms() -> None:
    query = _category_query("implementation_behavior")
    assert "self-monitoring" in query
    assert "implementation barrier" in query
    assert "meal planning" in query


def test_food_literacy_quick_mode_adds_culinary_and_commensality_terms() -> None:
    query = _category_query("food_literacy_culinary_commensality")
    assert "food agency" in query
    assert "meal preparation" in query
    assert "comensalidade" in query


def test_guidelines_queries_add_standards_of_care_and_pathway_terms() -> None:
    query = _category_query("guidelines_consensus").lower()

    assert "standards of care" in query
    assert "clinical pathway" in query
    assert "care pathway" in query
    assert "clinical decision pathway" in query
    assert "decision pathway" in query
    assert "joint guideline" in query
    assert "living guideline" in query


def test_guideline_like_priority_covers_standards_of_care_group() -> None:
    queries = build_watch_queries(["guidelines_consensus"], since_days=7, mode="quick")

    assert queries[1]["priority"] == 1


def test_quick_mode_diet_pattern_queries_cover_long_form_pattern_variants() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "mediterranean dietary pattern" in rendered
    assert "dietary approaches to stop hypertension" in rendered
    assert "plant based diet" in rendered
    assert "new nordic diet" in rendered


def test_quick_mode_interleaves_categories_so_tail_categories_survive() -> None:
    queries = build_watch_queries(None, since_days=7, mode="quick")
    first_seven_categories = [query["category"] for query in queries[:7]]

    assert len(set(first_seven_categories)) == 7
    assert first_seven_categories[0] == "guidelines_consensus"
    assert "frameworks_instruments" in first_seven_categories
    assert "implementation_behavior" in first_seven_categories


def test_selected_categories_preserve_round_robin_order_within_priority() -> None:
    queries = build_watch_queries(
        [
            "guidelines_consensus",
            "implementation_behavior",
            "frameworks_instruments",
        ],
        since_days=7,
        mode="quick",
    )

    assert [query["category"] for query in queries[:3]] == [
        "guidelines_consensus",
        "implementation_behavior",
        "frameworks_instruments",
    ]


def test_exhaustive_mode_food_literacy_queries_cover_labeling_terms() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=7,
        mode="exhaustive",
    )
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert len(queries) == 10
    assert "nutrition label" in rendered
    assert "label reading" in rendered
    assert "front-of-pack" in rendered
    assert "front-of-pack labeling" in rendered


def test_quick_mode_implementation_queries_cover_process_and_framework_terms() -> None:
    query = _category_query("implementation_behavior")

    assert "process evaluation" in query
    assert "implementation barriers" in query
    assert "implementation facilitators" in query
    assert "practice facilitation" in query
    assert "health coaching" in query
    assert "CFIR" in query
    assert "RE-AIM" in query


def test_quick_mode_implementation_queries_keep_three_seed_buckets() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")

    assert len(queries) == 3


def test_thesis_mode_implementation_queries_keep_curated_seed_order() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="thesis")
    rendered = [str(row["query"]).lower() for row in queries]

    assert len(rendered) == 6
    assert '"adherence"' in rendered[0]
    assert '"dietary adherence"' in rendered[1]
    assert '"implementation science"' in rendered[2]


def test_thesis_mode_implementation_queries_cover_food_access_program_variants() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="thesis")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "healthy food incentives" in rendered
    assert "nutrition incentives" in rendered
    assert "produce voucher" in rendered
    assert "fruit and vegetable vouchers" in rendered
    assert "medically tailored pantry" in rendered
    assert "medically tailored food packages" in rendered


def test_exhaustive_mode_implementation_queries_reach_framework_markers() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="exhaustive")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert '"cfir"' in rendered
    assert '"re-aim"' in rendered
    assert '"hybrid effectiveness-implementation"' in rendered


def test_implementation_queries_add_pipeline_aligned_operational_terms() -> None:
    query = _category_query("implementation_behavior").lower()

    assert "consolidated framework for implementation research" in query
    assert "implementation strategies" in query
    assert "audit and feedback" in query
    assert "service delivery" in query
    assert "care delivery" in query


def test_thesis_mode_food_literacy_queries_include_operational_shopping_terms() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=30,
        mode="thesis",
    )
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert '"food label literacy"' in rendered
    assert '"shopping skills"' in rendered


def test_exhaustive_mode_food_literacy_queries_include_budgeting_and_menu_terms() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=30,
        mode="exhaustive",
    )
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert '"food budgeting"' in rendered
    assert '"menu labeling"' in rendered
