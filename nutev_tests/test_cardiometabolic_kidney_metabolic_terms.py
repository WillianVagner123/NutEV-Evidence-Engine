from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2a_semantic_terms_include_ckm_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}

    assert "cardiovascular-kidney-metabolic syndrome" in terms
    assert "cardiovascular kidney metabolic syndrome" in terms
    assert "ckm syndrome" in terms


def test_busca2b_semantic_terms_include_ckm_nutrition_and_lifestyle_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    assert "cardiovascular-kidney-metabolic nutrition" in terms
    assert "cardiovascular kidney metabolic dietary intervention" in terms
    assert "ckm nutrition" in terms
    assert "ckm lifestyle intervention" in terms


def test_busca2b_semantic_document_terms_include_ckm_evidence_types() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", field="document_terms", min_priority=5)}

    assert "presidential advisory" in terms
    assert "clinical decision pathway" in terms
    assert "cardiovascular-kidney-metabolic nutrition guideline" in terms
    assert "ckm dietary intervention trial" in terms
