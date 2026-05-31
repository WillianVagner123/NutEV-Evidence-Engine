from __future__ import annotations

from nutev.querypacks import semantic_extensions  # noqa: F401
from nutev.querypacks.semantic_blocks import SEMANTIC_RESEARCH_BLOCKS


def test_food_environment_terms_extend_food_literacy_block() -> None:
    block = SEMANTIC_RESEARCH_BLOCKS["food_literacy_agency"]
    terms = {term.lower() for term in block["terms"]}
    document_terms = {term.lower() for term in block["document_terms"]}

    assert "food environment assessment" in terms
    assert "healthy food retail intervention" in terms
    assert "food pantry nutrition" in terms
    assert "food desert" in terms
    assert "diet quality index" in terms
    assert "healthy eating index" in document_terms


def test_food_environment_terms_extend_adherence_precision_block_without_duplicates() -> None:
    block = SEMANTIC_RESEARCH_BLOCKS["adherence_persistence"]
    lowered_terms = [term.lower() for term in block["terms"]]
    lowered_document_terms = [term.lower() for term in block["document_terms"]]

    assert "food environment intervention" in lowered_terms
    assert "alternative healthy eating index" in lowered_terms
    assert "supermarket intervention" in lowered_document_terms
    assert len(lowered_terms) == len(set(lowered_terms))
    assert len(lowered_document_terms) == len(set(lowered_document_terms))
