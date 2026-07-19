"""Evidence Gems Bank (§14): descriptive-value ranking, not a quality score."""
from __future__ import annotations

from nutev.analysis.evidence_gems import (
    best_gems_markdown,
    gem_row,
    rank_gems,
    score_gem,
)


def _rich_doc():
    # A high-value doc: authoritative, current, integrates A/B/C/D, operationalized.
    return {
        "name": "Guia Alimentar", "country": "brazil", "authority": "tier_1",
        "reference_version": "2024", "doc_type": "guideline",
        "themes_present": "implementation:adherence|diet_patterns:mediterranean",
        "reference": "MoH. Guia Alimentar. Brazil. 2024.",
        "domain_A_state": "RECOMMENDED", "domain_A_intensity": 2, "domain_A_evidence": "recommends more fruit and vegetables", "domain_A_page": 3,
        "domain_B_state": "OPERATIONALIZED", "domain_B_intensity": 3, "domain_B_evidence": "a step-by-step meal planning toolkit", "domain_B_page": 5,
        "domain_C_state": "RECOMMENDED", "domain_C_intensity": 2, "domain_C_evidence": "share meals together", "domain_C_page": 7,
        "domain_D_state": "OPERATIONALIZED", "domain_D_intensity": 3, "domain_D_evidence": "monitoring indicators for adherence", "domain_D_page": 9,
    }


def _thin_doc():
    return {
        "name": "US brief", "country": "usa", "authority": "",
        "reference_version": "2010", "doc_type": "other",
        "domain_A_state": "NOT_ASSESSED", "domain_A_intensity": "",
        "domain_B_state": "MENTIONED", "domain_B_intensity": 1,
        "domain_C_state": "NOT_ASSESSED", "domain_C_intensity": "",
        "domain_D_state": "NOT_ASSESSED", "domain_D_intensity": "",
    }


def test_rich_doc_scores_high_with_breakdown():
    s = score_gem(_rich_doc())
    assert s["gem_score"] >= 12
    b = s["breakdown"]
    assert b["authority"] == 3
    assert b["currency"] == 2
    assert b["integration_breadth"] == 4      # all four domains recommended+
    assert b["operational_specificity"] >= 2  # B and D operationalized
    assert b["traceability"] == 2             # snippet + page
    assert s["source_snippet"]                # best evidence carried
    assert s["gem_score"] <= 18


def test_thin_doc_scores_low():
    assert score_gem(_thin_doc())["gem_score"] <= 3


def test_rank_orders_and_filters():
    gems = rank_gems([_thin_doc(), _rich_doc()], min_score=1)
    assert gems[0]["name"] == "Guia Alimentar"  # richest first
    assert gems[0]["rank"] == 1
    # A gem is explicitly descriptive value, not a quality/risk-of-bias score.
    assert "NÃO é avaliação de qualidade" in gems[0]["limitations"]
    assert gems[0]["proposed_claim"] == ""       # human writes the paraphrase
    assert gems[0]["needs_human_review"] is True


def test_gem_row_has_source_and_section():
    row = gem_row(_rich_doc())
    assert row["source_snippet"] and row["source_page"] in (3, 5, 7, 9)
    assert row["manuscript_section"]
    assert row["reference"].startswith("MoH.")


def test_best_gems_markdown_carries_warning_and_snippets():
    md = best_gems_markdown(rank_gems([_rich_doc()]))
    assert "NÃO é avaliação de qualidade" in md
    assert "Guia Alimentar" in md
    assert "Trecho" in md
