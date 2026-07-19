"""Protocol domain states + intensity (0-3) with traceable evidence (§7.2/§7.3, §18)."""
from __future__ import annotations

from nutev.analysis.domain_states import (
    STATE_MENTIONED,
    STATE_NOT_ASSESSED,
    STATE_OPERATIONALIZED,
    STATE_RECOMMENDED,
    code_domain_states,
    domain_state_rows,
)


def test_not_assessed_when_no_keyword_and_no_intensity():
    out = code_domain_states({"extracted_text": "The weather is nice and sunny today, nothing about food."})
    assert out["domain_A_state"] == STATE_NOT_ASSESSED
    # Machine NEVER asserts intensity 0 (that's a human "assessed & absent"); it's blank.
    assert out["domain_A_intensity"] == ""
    assert out["domain_A_evidence"] == ""


def test_mentioned_vs_recommended_vs_operationalized():
    text = (
        "Diet quality and nutrient intake vary across regions. "  # A: plain mention
        "Guidelines recommend more physical activity for everyone. "  # D-ish actionable... use B below
        "The guideline recommends increasing fruit and vegetable intake. "  # A recommended
        "A step-by-step meal planning toolkit and monitoring indicators support cooking skills."  # B operationalized
    )
    out = code_domain_states({"extracted_text": text})
    assert out["domain_A_state"] == STATE_RECOMMENDED and out["domain_A_intensity"] == 2
    assert out["domain_B_state"] == STATE_OPERATIONALIZED and out["domain_B_intensity"] == 3


def test_incidental_mention_is_only_mentioned():
    # §18.4 spirit: an incidental mention must not be inflated to a strong claim.
    out = code_domain_states({"extracted_text": "This national guide briefly notes the Mediterranean diet and dietary patterns in passing."})
    assert out["domain_A_state"] == STATE_MENTIONED
    assert out["domain_A_intensity"] == 1


def test_evidence_and_page_present_for_any_positive_state():
    # §18.7: no final code without a source snippet (and page when available).
    pages = [
        "Intro with no domain content here at all.",
        "The guideline recommends increasing fruit and vegetable intake for diet quality.",
    ]
    out = code_domain_states({"extracted_text": "\n".join(pages)}, pages=pages)
    assert out["domain_A_state"] == STATE_RECOMMENDED
    assert out["domain_A_evidence"]  # non-empty snippet
    assert out["domain_A_page"] == 2  # page-precise


def test_suggestion_is_marked_not_a_human_decision():
    out = code_domain_states({"extracted_text": "The guideline recommends fruit and vegetables."})
    assert out["domain_coding_source"] == "machine_suggestion"
    assert out["domain_states_need_review"] is True
    rows = domain_state_rows({"name": "X", **out})
    assert all(r["coding_source"] == "machine_suggestion" and r["needs_human_review"] for r in rows)


def test_empty_text_all_not_assessed():
    out = code_domain_states({})
    for d in ("A", "B", "C", "D"):
        assert out[f"domain_{d}_state"] == STATE_NOT_ASSESSED
        assert out[f"domain_{d}_intensity"] == ""


def test_domain_state_rows_shape():
    out = code_domain_states({"extracted_text": "Families should share meals together to strengthen commensality."})
    rows = domain_state_rows({"name": "G", "country": "BR", "reference": "MoH. 2014.", **out})
    assert len(rows) == 4
    c = [r for r in rows if r["domain"] == "C"][0]
    assert c["state"] in {STATE_MENTIONED, STATE_RECOMMENDED, STATE_OPERATIONALIZED}
    assert c["reference"] == "MoH. 2014."
