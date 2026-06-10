from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.querypacks.semantic_extensions import apply_semantic_extensions


def test_sustainable_diet_guidance_terms_are_semantic_search_terms():
    terms = set(semantic_terms("busca1"))
    document_terms = set(semantic_terms("busca1", field="document_terms"))

    assert "sustainable healthy diets" in terms
    assert "sustainable food-based dietary guideline" in terms
    assert "dietary guidelines sustainability" in terms
    assert "sustainable food-based dietary guideline" in document_terms
    assert "sustainable diets systematic review" in document_terms


def test_sustainable_diet_extension_is_idempotent():
    before = semantic_terms("busca1").count("sustainable healthy diets")

    apply_semantic_extensions()

    after = semantic_terms("busca1").count("sustainable healthy diets")
    assert before == 1
    assert after == 1
