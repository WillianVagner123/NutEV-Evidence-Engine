from __future__ import annotations

import nutev.querypacks  # noqa: F401 - applies semantic extensions on import
from nutev.querypacks.semantic_blocks import SEMANTIC_RESEARCH_BLOCKS


def _block_terms(block_name: str, field: str = "terms") -> set[str]:
    return {term.lower() for term in SEMANTIC_RESEARCH_BLOCKS[block_name][field]}


def test_food_access_extensions_cover_grocery_prescription_and_food_farmacy() -> None:
    terms = _block_terms("food_prescription_programs")

    assert "grocery prescription" in terms
    assert "grocery prescription program" in terms
    assert "food farmacy" in terms
    assert "food farmacy program" in terms
    assert "healthy food box" in terms


def test_food_access_document_terms_cover_implementation_and_evaluation() -> None:
    document_terms = _block_terms("implementation_science", "document_terms")

    assert "grocery prescription implementation study" in document_terms
    assert "grocery prescription program evaluation" in document_terms
    assert "food farmacy implementation study" in document_terms
    assert "food farmacy program evaluation" in document_terms
    assert "healthy food box intervention trial" in document_terms
