from __future__ import annotations

from nutev.querypacks.builders import (
    METABOLIC_REMISSION_DOCUMENT_TERMS,
    METABOLIC_REMISSION_TERMS,
    METABOLIC_REMISSION_WEB_HINTS,
)


def test_metabolic_remission_terms_cover_guidelines_reviews_and_trials() -> None:
    assert "type 2 diabetes remission" in METABOLIC_REMISSION_TERMS
    assert "type 2 diabetes reversal" in METABOLIC_REMISSION_TERMS
    assert "low energy diet remission" in METABOLIC_REMISSION_TERMS
    assert "total diet replacement remission" in METABOLIC_REMISSION_TERMS
    assert "meal replacement remission" in METABOLIC_REMISSION_TERMS
    assert "weight maintenance intervention" in METABOLIC_REMISSION_TERMS

    assert "diabetes remission clinical practice guideline" in METABOLIC_REMISSION_WEB_HINTS
    assert "diabetes remission systematic review" in METABOLIC_REMISSION_WEB_HINTS
    assert "low energy diet remission trial" in METABOLIC_REMISSION_WEB_HINTS
    assert "meal replacement remission trial" in METABOLIC_REMISSION_WEB_HINTS

    assert "remission systematic review" in METABOLIC_REMISSION_DOCUMENT_TERMS
    assert "remission trial" in METABOLIC_REMISSION_DOCUMENT_TERMS
    assert "diabetes remission trial" in METABOLIC_REMISSION_DOCUMENT_TERMS
