from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2a_semantic_terms_include_ckm_disease_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}

    assert "cardiovascular-kidney-metabolic disease" in terms
    assert "cardio-kidney-metabolic syndrome" in terms
    assert "ckm disease" in terms


def test_busca2b_document_terms_include_ckm_advisory_variants() -> None:
    terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=5)
    }

    assert "aha presidential advisory" in terms
    assert "cardiovascular-kidney-metabolic presidential advisory" in terms
    assert "ckm health framework" in terms
