from nutev.querypacks.processing_quality_extensions import apply_processing_quality_extensions
from nutev.querypacks.semantic_blocks import semantic_terms


def test_processing_quality_extensions_add_recent_food_processing_terms():
    apply_processing_quality_extensions()
    terms = semantic_terms("busca2b", min_priority=5)
    assert "nova group 4" in terms
    assert "ultra-processed dietary pattern" in terms
    assert "highly processed foods" in terms


def test_processing_quality_extensions_are_idempotent():
    apply_processing_quality_extensions()
    apply_processing_quality_extensions()
    terms = semantic_terms("busca2b", min_priority=5)
    assert terms.count("nova group 4") == 1
