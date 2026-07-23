from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.portfolio_lipid_extensions import (
    PORTFOLIO_LIPID_PATTERN_DOCUMENT_TERMS,
    PORTFOLIO_LIPID_PATTERN_TERMS,
    apply_portfolio_lipid_extensions,
)


def test_portfolio_lipid_extension_adds_pattern_and_lipid_terms() -> None:
    apply_portfolio_lipid_extensions()

    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["portfolio_lipid_pattern"]
    terms = {term.lower() for term in block["terms"]}
    document_terms = {term.lower() for term in block["document_terms"]}

    assert "portfolio dietary pattern" in terms
    assert "ldl cholesterol lowering diet" in terms
    assert "dietary portfolio for cardiometabolic risk" in terms
    assert "plant sterols" in terms
    assert "portfolio diet systematic review" in document_terms
    assert "ldl cholesterol lowering diet trial" in document_terms


def test_portfolio_lipid_extension_is_idempotent() -> None:
    apply_portfolio_lipid_extensions()
    apply_portfolio_lipid_extensions()

    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["portfolio_lipid_pattern"]
    assert len(block["terms"]) == len({term.lower() for term in block["terms"]})
    assert len(block["document_terms"]) == len(
        {term.lower() for term in block["document_terms"]}
    )
    assert set(PORTFOLIO_LIPID_PATTERN_TERMS).issubset(set(block["terms"]))
    assert set(PORTFOLIO_LIPID_PATTERN_DOCUMENT_TERMS).issubset(
        set(block["document_terms"])
    )


def test_clinical_workstreams_prioritize_portfolio_lipid_terms() -> None:
    apply_portfolio_lipid_extensions()

    busca2a_terms = " ".join(semantic_blocks.semantic_terms("busca2a", min_priority=5))
    busca2b_docs = " ".join(
        semantic_blocks.semantic_terms(
            "busca2b",
            field="document_terms",
            min_priority=5,
        )
    )

    assert "portfolio dietary pattern" in busca2a_terms
    assert "dietary portfolio for dyslipidemia" in busca2a_terms
    assert "portfolio diet intervention trial" in busca2b_docs
    assert "lipid-lowering dietary pattern trial" in busca2b_docs
