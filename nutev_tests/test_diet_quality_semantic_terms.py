from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2b_semantic_terms_include_diet_quality_indices() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    assert "healthy eating index" in terms
    assert "alternate healthy eating index" in terms
    assert "diet quality index" in terms
    assert "dietary inflammatory index" in terms


def test_busca1_semantic_terms_include_prudent_and_inflammatory_patterns() -> None:
    terms = {term.lower() for term in semantic_terms("busca1", min_priority=5)}

    assert "anti-inflammatory diet" in terms
    assert "anti inflammatory diet" in terms
    assert "prudent dietary pattern" in terms
    assert "western dietary pattern" in terms


def test_diet_quality_document_terms_keep_evidence_synthesis_focus() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", field="document_terms", min_priority=5)}

    assert "umbrella review" in terms
    assert "food-based dietary guideline" in terms
