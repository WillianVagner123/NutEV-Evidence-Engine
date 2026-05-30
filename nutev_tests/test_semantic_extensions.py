from __future__ import annotations

from nutev.querypacks.semantic_blocks import SEMANTIC_RESEARCH_BLOCKS, semantic_terms
from nutev.querypacks.semantic_extensions import apply_semantic_extensions


def test_semantic_extensions_add_nutrition_anchored_adherence_terms() -> None:
    apply_semantic_extensions()

    busca2b_terms = semantic_terms("busca2b", min_priority=5)
    assert "digital nutrition intervention" in busca2b_terms
    assert "mobile dietary self-monitoring" in busca2b_terms
    assert "food pharmacy program" in busca2b_terms


def test_semantic_extensions_are_idempotent() -> None:
    apply_semantic_extensions()
    apply_semantic_extensions()

    terms = SEMANTIC_RESEARCH_BLOCKS["adherence_persistence"]["terms"]
    assert terms.count("digital dietary intervention") == 1

    food_terms = SEMANTIC_RESEARCH_BLOCKS["food_prescription_programs"]["terms"]
    assert food_terms.count("produce prescription intervention") == 1
