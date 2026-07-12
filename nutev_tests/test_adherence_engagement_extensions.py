from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.adherence_engagement_extensions import (
    ADHERENCE_ENGAGEMENT_DOCUMENT_TERMS,
    ADHERENCE_ENGAGEMENT_TERMS,
    apply_adherence_engagement_extensions,
)


def test_adherence_engagement_extension_adds_dose_and_retention_terms() -> None:
    apply_adherence_engagement_extensions()

    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["adherence_engagement_dose"]
    terms = {term.lower() for term in block["terms"]}
    document_terms = {term.lower() for term in block["document_terms"]}

    assert "dietary intervention engagement" in terms
    assert "nutrition intervention retention" in terms
    assert "dietary intervention dose" in terms
    assert "session attendance" in terms
    assert "dietary intervention dose trial" in document_terms
    assert "adherence monitoring intervention" in document_terms


def test_adherence_engagement_extension_is_idempotent() -> None:
    apply_adherence_engagement_extensions()
    apply_adherence_engagement_extensions()

    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["adherence_engagement_dose"]
    assert len(block["terms"]) == len({term.lower() for term in block["terms"]})
    assert len(block["document_terms"]) == len(
        {term.lower() for term in block["document_terms"]}
    )
    assert set(ADHERENCE_ENGAGEMENT_TERMS).issubset(set(block["terms"]))
    assert set(ADHERENCE_ENGAGEMENT_DOCUMENT_TERMS).issubset(
        set(block["document_terms"])
    )


def test_busca2b_prioritizes_adherence_engagement_terms() -> None:
    apply_adherence_engagement_extensions()

    rendered = " ".join(semantic_blocks.semantic_terms("busca2b", min_priority=5))

    assert "dietary intervention engagement" in rendered
    assert "nutrition intervention retention" in rendered
    assert "intervention dose" in rendered
