from __future__ import annotations

from nutev.querypacks.diet_pattern_extensions import apply_diet_pattern_extensions
from nutev.querypacks.semantic_blocks import semantic_terms


def test_diet_pattern_extensions_feed_priority_workstreams() -> None:
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}
    busca2a_terms = {term.lower() for term in semantic_terms("busca2a", min_priority=4)}

    assert "portfolio dietary pattern" in busca2b_terms
    assert "healthy plant-based diet index" in busca2b_terms
    assert "planetary health diet index" in busca2b_terms
    assert "dietary portfolio" in busca2a_terms


def test_diet_pattern_extension_is_idempotent() -> None:
    apply_diet_pattern_extensions()
    apply_diet_pattern_extensions()

    terms = [term.lower() for term in semantic_terms("busca2b", min_priority=5)]

    assert terms.count("portfolio dietary pattern") == 1
    assert terms.count("healthy plant-based diet index") == 1
