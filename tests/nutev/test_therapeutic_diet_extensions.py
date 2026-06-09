from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2b_semantic_terms_include_therapeutic_diet_replacements() -> None:
    terms = semantic_terms("busca2b", min_priority=5)
    document_terms = semantic_terms("busca2b", field="document_terms", min_priority=5)

    assert "total diet replacement" in terms
    assert "very-low-energy diet" in terms
    assert "partial meal replacement" in terms
    assert "total diet replacement trial" in document_terms
    assert "diabetes remission diet trial" in document_terms
