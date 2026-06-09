from nutev.global_watch.watch_config import WATCH_CATEGORIES


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
