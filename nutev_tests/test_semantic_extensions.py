from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.semantic_extensions import apply_semantic_extensions


def _terms(block_name: str) -> set[str]:
    return {
        term.lower()
        for term in semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name]["terms"]
    }


def _document_terms(block_name: str) -> set[str]:
    return {
        term.lower()
        for term in semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name]["document_terms"]
    }


def test_diet_quality_terms_extend_adherence_and_lifestyle_blocks() -> None:
    apply_semantic_extensions()

    for block_name in ("adherence_persistence", "lifestyle_nutrition_patterns"):
        terms = _terms(block_name)
        assert "diet quality" in terms
        assert "dietary quality" in terms
        assert "healthy eating index 2015" in terms
        assert "alternate healthy eating index 2010" in terms
        assert "dietary inflammatory index" in terms
        assert "dietary diversity score" in terms


def test_diet_quality_document_terms_cover_validation_variants() -> None:
    apply_semantic_extensions()

    document_terms = _document_terms("adherence_persistence")
    assert "healthy eating index 2015 validation" in document_terms
    assert "alternate healthy eating index validation" in document_terms
    assert "dietary inflammatory index validation" in document_terms


def test_semantic_extensions_are_idempotent_for_diet_quality_terms() -> None:
    apply_semantic_extensions()
    before = len(semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["adherence_persistence"]["terms"])

    apply_semantic_extensions()
    after = len(semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["adherence_persistence"]["terms"])

    assert after == before
