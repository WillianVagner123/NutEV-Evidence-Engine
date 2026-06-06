from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca1_includes_sustainable_healthy_diet_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca1", min_priority=5)}
    document_terms = {
        term.lower()
        for term in semantic_terms("busca1", field="document_terms", min_priority=5)
    }

    assert "sustainable healthy diet" in terms
    assert "healthy and sustainable diets" in terms
    assert "sustainable dietary patterns" in terms
    assert "sustainable healthy diet guideline" in document_terms
    assert "planetary health diet guideline" in document_terms


def test_busca2b_includes_sustainable_healthy_diet_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    assert "sustainable healthy diets" in terms
    assert "healthy sustainable diet" in terms
