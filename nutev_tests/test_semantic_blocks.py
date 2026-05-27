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
