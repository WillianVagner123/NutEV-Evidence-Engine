from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries


def test_watch_categories_include_nutrition_prescription_terms() -> None:
    expected_terms = {
        "nutrition prescription",
        "dietary prescription",
        "food prescription",
        "personalized meal planning",
        "individualized meal plan",
    }

    for category in (
        "lifestyle_medicine",
        "diet_patterns",
        "implementation_behavior",
    ):
        terms = {term.lower() for term in WATCH_CATEGORIES[category]}
        assert expected_terms & terms


def test_watch_categories_include_food_access_prescription_variants() -> None:
    expected_terms = {
        "healthy food incentive",
        "healthy food incentives",
        "nutrition incentive",
        "nutrition incentives",
        "produce voucher",
        "produce vouchers",
        "fruit and vegetable voucher",
        "fruit and vegetable vouchers",
        "medically tailored pantry",
        "medically tailored pantries",
        "medically tailored food package",
        "medically tailored food packages",
    }

    for category in ("lifestyle_medicine", "implementation_behavior"):
        terms = {term.lower() for term in WATCH_CATEGORIES[category]}
        assert expected_terms <= terms


def test_obesity_cardiometabolic_watch_terms_include_precise_lipid_markers() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    assert "atherogenic dyslipidemia" in terms
    assert "atherogenic dyslipidaemia" in terms
    assert "ldl cholesterol" in terms
    assert "non-hdl cholesterol" in terms
    assert "non hdl cholesterol" in terms
    assert "lipid lowering" in terms
    assert "triglyceride lowering" in terms


def test_watch_categories_include_nutrition_care_pathway_terms() -> None:
    expected_terms = {
        "medical nutrition therapy guideline",
        "medical nutrition therapy consensus",
        "nutrition care consensus",
        "nutrition care pathway guideline",
        "nutrition care protocol guideline",
    }

    for category in ("guidelines_consensus", "lifestyle_medicine"):
        terms = {term.lower() for term in WATCH_CATEGORIES[category]}
        assert expected_terms <= terms


def test_nutrition_care_pathway_quick_watch_query_is_generated() -> None:
    queries = build_watch_queries(["guidelines_consensus"], since_days=30, mode="quick")
    query_text = "\n".join(str(item["query"]).lower() for item in queries)

    assert queries
    assert "nutrition care pathway" in query_text
    assert "medical nutrition therapy" in query_text
