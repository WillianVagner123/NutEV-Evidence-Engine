from nutev.querypacks import apply_sustainable_diet_extensions
from nutev.querypacks.semantic_blocks import semantic_terms


def test_sustainable_diet_terms_extend_high_priority_nutrition_patterns() -> None:
    apply_sustainable_diet_extensions()

    busca1_terms = {term.lower() for term in semantic_terms("busca1")}
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b")}
    busca2b_document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms")
    }

    for expected in (
        "sustainable healthy diet",
        "healthy and sustainable diets",
        "sustainable dietary patterns",
        "planetary health diets",
        "eat-lancet reference diet",
    ):
        assert expected in busca1_terms
        assert expected in busca2b_terms

    assert "sustainable dietary patterns systematic review" in busca2b_document_terms
    assert "planetary health diet systematic review" in busca2b_document_terms
    assert "eat-lancet reference diet systematic review" in busca2b_document_terms
