from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2a_semantic_terms_include_ckm_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}

    assert "cardiovascular-kidney-metabolic syndrome" in terms
    assert "cardiovascular kidney metabolic syndrome" in terms
    assert "ckm syndrome" in terms


def test_busca2b_semantic_document_terms_include_ckm_evidence_types() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", field="document_terms", min_priority=5)}

    assert "presidential advisory" in terms
    assert "clinical decision pathway" in terms


def test_busca2a_and_busca2b_semantic_terms_include_cardiorenal_variants() -> None:
    busca2a_terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    for terms in (busca2a_terms, busca2b_terms):
        assert "cardiorenal metabolic syndrome" in terms
        assert "cardio-renal-metabolic syndrome" in terms
        assert "cardiorenal-metabolic syndrome" in terms
        assert "cardiorenal metabolic risk" in terms


def test_busca2b_semantic_document_terms_include_cardiorenal_nutrition_hooks() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", field="document_terms", min_priority=5)}

    assert "cardiorenal metabolic syndrome nutrition intervention" in terms
    assert "cardiorenal metabolic syndrome dietary intervention" in terms
