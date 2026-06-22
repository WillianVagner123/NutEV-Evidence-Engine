from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.food_insecurity_referral_extensions import (
    apply_food_insecurity_referral_extensions,
)


def test_food_insecurity_referral_terms_extend_relevant_semantic_blocks() -> None:
    apply_food_insecurity_referral_extensions()

    for block_name in ("equity_access", "food_prescription_programs", "implementation_science"):
        block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name]
        assert "food insecurity screening and referral" in block["terms"]
        assert "food resource navigation" in block["terms"]
        assert "food insecurity referral implementation study" in block["document_terms"]


def test_food_insecurity_referral_extension_is_idempotent() -> None:
    apply_food_insecurity_referral_extensions()
    apply_food_insecurity_referral_extensions()

    terms = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["equity_access"]["terms"]
    assert terms.count("food resource navigation") == 1
