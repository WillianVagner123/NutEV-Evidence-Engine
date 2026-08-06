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


def test_food_access_navigation_terms_reach_high_priority_querypacks() -> None:
    busca1_terms = {term.lower() for term in semantic_terms("busca1", min_priority=5)}
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}
    busca2b_document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=5)
    }

    assert "food resource navigation" in busca1_terms
    assert "fresh produce prescription" in busca1_terms
    assert "medically tailored nutrition" in busca2b_terms
    assert "nutrition assistance intervention" in busca2b_terms
    assert "food resource navigation program evaluation" in busca2b_document_terms
    assert "medically tailored nutrition intervention trial" in busca2b_document_terms


def test_busca2b_semantic_terms_include_group_visit_care_delivery() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    assert "shared medical appointments" in terms
    assert "group medical visits" in terms
    assert "group nutrition counseling" in terms
    assert "group diabetes prevention program" in terms


def test_group_visit_care_delivery_is_prioritized_for_intervention_workstream() -> None:
    blocks = prioritized_semantic_blocks("busca2b")

    assert {"name": "group_visit_care_delivery", "priority": 5} in blocks
