from __future__ import annotations

from nutev.querypacks import apply_semantic_extensions
from nutev.querypacks.semantic_blocks import SEMANTIC_RESEARCH_BLOCKS


def _block_terms(block_name: str) -> tuple[list[str], list[str]]:
    block = SEMANTIC_RESEARCH_BLOCKS[block_name]
    return block["terms"], block["document_terms"]


def test_ckm_nutrition_terms_extend_cardiometabolic_and_nutrition_blocks() -> None:
    cardiometabolic_terms, cardiometabolic_docs = _block_terms(
        "cardiometabolic_precision"
    )
    nutrition_terms, nutrition_docs = _block_terms("nutrition_care_delivery")
    lifestyle_terms, _ = _block_terms("lifestyle_nutrition_patterns")

    assert "ckm nutrition" in cardiometabolic_terms
    assert "ckm nutrition" in nutrition_terms
    assert "ckm nutrition" in lifestyle_terms
    assert "cardiovascular-kidney-metabolic dietary guideline" in cardiometabolic_docs
    assert "cardiovascular-kidney-metabolic dietary guideline" in nutrition_docs


def test_ckm_semantic_extension_is_idempotent() -> None:
    terms_before, docs_before = _block_terms("cardiometabolic_precision")
    term_count = terms_before.count("ckm nutrition")
    doc_count = docs_before.count("ckm nutrition guideline")

    apply_semantic_extensions()

    terms_after, docs_after = _block_terms("cardiometabolic_precision")
    assert terms_after.count("ckm nutrition") == term_count
    assert docs_after.count("ckm nutrition guideline") == doc_count
