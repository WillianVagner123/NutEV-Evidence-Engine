from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2a_semantic_terms_include_sarcopenic_obesity_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}

    assert "sarcopenic obesity" in terms
    assert "sarcopenic adiposity" in terms
    assert "obesity with sarcopenia" in terms
    assert "dynapenic obesity" in terms


def test_busca2b_semantic_document_terms_include_sarcopenic_evidence_types() -> None:
    terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=5)
    }

    assert "position statement" in terms
    assert "umbrella review" in terms
