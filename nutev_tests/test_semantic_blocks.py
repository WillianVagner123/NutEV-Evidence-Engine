from nutev.querypacks.semantic_blocks import prioritized_semantic_blocks, semantic_terms


def test_busca2a_prioritizes_cardiometabolic_precision_block() -> None:
    blocks = prioritized_semantic_blocks("busca2a")
    assert {"name": "cardiometabolic_precision", "priority": 5} in blocks


def test_busca2b_semantic_terms_include_precision_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}
    assert "prediabetes" in terms
    assert "insulin resistance" in terms
    assert "adiposity-based chronic disease" in terms
    assert "hypercholesterolaemia" in terms


def test_busca2b_semantic_terms_include_behavior_change_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}
    assert "behavior change techniques" in terms
    assert "behaviour change techniques" in terms
    assert "behavior change taxonomy" in terms
    assert "com b" in terms


def test_busca2b_semantic_terms_include_nutrition_care_process_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}
    assert "nutrition care process" in terms
    assert "registered dietitian-led intervention" in terms
    assert "dietitian-delivered intervention" in terms


def test_busca2a_semantic_document_terms_include_nutrition_care_pathway() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", field="document_terms", min_priority=4)}
    assert "nutrition care process model" in terms
    assert "nutrition care pathway" in terms


def test_busca2b_priority_five_terms_surface_nutrition_care_delivery_before_generic_implementation() -> None:
    terms = semantic_terms("busca2b", min_priority=5)

    assert terms.index("nutrition care pathway") < terms.index("implementation science")
    assert terms.index("registered dietitian-led intervention") < terms.index(
        "shared decision making"
    )


def test_a3_alias_priority_five_terms_include_nutrition_care_delivery() -> None:
    terms = {term.lower() for term in semantic_terms("a3", min_priority=5)}

    assert "nutrition care pathway" in terms
    assert "registered dietitian-led intervention" in terms


def test_busca1_semantic_terms_include_food_as_medicine_program_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca1", min_priority=5)}

    assert "healthy food incentive program" in terms
    assert "nutrition incentive program" in terms
    assert "produce voucher program" in terms
    assert "fruit and vegetable voucher program" in terms


def test_busca2b_semantic_terms_include_food_as_medicine_program_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    assert "healthy food incentive program" in terms
    assert "nutrition incentive program" in terms
    assert "produce voucher program" in terms
    assert "fruit and vegetable voucher program" in terms


def test_busca1_semantic_terms_include_nutrition_insecurity_access_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca1", min_priority=3)}

    assert "nutrition insecurity" in terms
    assert "nutrition insecurity screening" in terms
    assert "screening for nutrition insecurity" in terms
    assert "food and nutrition security" in terms
    assert "food and nutrition insecurity" in terms


def test_busca2b_semantic_terms_include_food_access_navigation_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}

    assert "food resource navigation" in terms
    assert "fresh food pharmacy" in terms
    assert "fruit and vegetable incentives" in terms


def test_busca2b_semantic_document_terms_include_nutrition_insecurity_programs() -> None:
    terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=4)
    }

    assert "nutrition insecurity screening program" in terms
    assert "nutrition insecurity intervention" in terms
    assert "food and nutrition security intervention" in terms
    assert "fresh food pharmacy program" in terms
