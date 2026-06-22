from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2a_semantic_terms_include_ckm_nutrition_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}

    assert "cardiovascular-kidney-metabolic nutrition" in terms
    assert "ckm risk management" in terms


def test_busca2b_semantic_document_terms_include_ckm_guidance_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", field="document_terms", min_priority=5)}

    assert "ckm scientific statement" in terms
    assert "cardiovascular-kidney-metabolic clinical decision pathway" in terms
