"""Two-reviewer screening flow (§13): reconcile, adjudicate, kappa, export gate."""
from __future__ import annotations

import pytest

from nutev.review.screening import (
    adjudicate,
    build_screening_queue,
    cohen_kappa,
    export_blocked_reason,
    final_decision,
    is_export_ready,
    reconcile_record,
)


def _d(reviewer, decision, phase="full_text"):
    return {"reviewer": reviewer, "decision": decision, "phase": phase}


def test_needs_second_reviewer_with_one():
    assert reconcile_record([_d("R1", "include")], "full_text")["status"] == "needs_second_reviewer"


def test_agreement_and_conflict():
    assert reconcile_record([_d("R1", "include"), _d("R2", "include")], "full_text")["status"] == "agree_include"
    assert reconcile_record([_d("R1", "exclude"), _d("R2", "exclude")], "full_text")["status"] == "agree_exclude"
    assert reconcile_record([_d("R1", "include"), _d("R2", "exclude")], "full_text")["status"] == "conflict"
    # 'uncertain' is a conflict, never a silent decision.
    assert reconcile_record([_d("R1", "include"), _d("R2", "uncertain")], "full_text")["status"] == "conflict"


def test_export_gate_blocks_until_validated():
    # Not validated -> blocked.
    assert is_export_ready([_d("R1", "include")]) is False
    assert "not validated" in export_blocked_reason([_d("R1", "include")])
    # Agreement to include -> export ready.
    decs = [_d("R1", "include"), _d("R2", "include")]
    assert is_export_ready(decs) is True
    assert export_blocked_reason(decs) == ""
    # Agreement to exclude -> blocked with reason.
    assert is_export_ready([_d("R1", "exclude"), _d("R2", "exclude")]) is False


def test_conflict_resolved_by_adjudication():
    decs = [_d("R1", "include"), _d("R2", "exclude")]
    assert final_decision(decs)["decision"] == "pending"
    adj = adjudicate("doc1", "full_text", "advisor", "include", "guideline in scope, adults")
    fd = final_decision(decs, [adj])
    assert fd["decision"] == "include" and fd["basis"] == "adjudication"
    assert is_export_ready(decs, [adj]) is True


def test_adjudication_requires_rationale():
    with pytest.raises(ValueError):
        adjudicate("d", "full_text", "advisor", "include", "")
    with pytest.raises(ValueError):
        adjudicate("d", "full_text", "advisor", "maybe", "because")


def test_cohen_kappa_perfect_and_chance():
    perfect = [("include", "include"), ("exclude", "exclude"), ("include", "include")]
    assert cohen_kappa(perfect) == 1.0
    # Total disagreement on a 2-class split -> kappa <= 0.
    disagree = [("include", "exclude"), ("exclude", "include")]
    assert cohen_kappa(disagree) <= 0.0
    assert cohen_kappa([]) == 0.0


def test_screening_queue_flags_no_full_text():
    rows = [
        {"name": "ok guide", "extraction_status": "ok"},
        {"name": "scanned", "extraction_status": "pdf_needs_ocr_setup"},
        {"name": "blocked", "extraction_status": "junk_or_blocked"},
    ]
    q = build_screening_queue(rows)
    flags = {r["name"]: r["screen_flag"] for r in q}
    assert flags["ok guide"] == "ready_to_screen"
    assert flags["scanned"] == "poor_ocr"
    assert flags["blocked"] == "no_full_text"
    # Nothing is export-ready straight out of the pipeline.
    assert all(r["export_ready"] is False for r in q)


# --------------------------------------------------------------------------- #
# Inter-reviewer agreement report (screening_agreement) — C5.
# --------------------------------------------------------------------------- #

from nutev.review.screening import queue_reviewer_pairs, screening_agreement  # noqa: E402


def _q(r1="", r2="", flag="ready_to_screen", export_ready=False):
    return {
        "reviewer_1_decision": r1,
        "reviewer_2_decision": r2,
        "screen_flag": flag,
        "export_ready": export_ready,
    }


def test_agreement_empty_queue_is_wellformed_zero_report():
    rep = screening_agreement([])
    assert rep["n_items"] == 0
    assert rep["n_double_screened"] == 0
    assert rep["cohen_kappa"] is None
    assert rep["percent_agreement"] is None
    assert "once two reviewers" in rep["note"]


def test_agreement_fresh_queue_has_no_pairs_yet():
    # A freshly built queue has blank reviewer decisions → no kappa yet.
    rep = screening_agreement(build_screening_queue([{"name": "g1", "extraction_status": "ok"}]))
    assert rep["n_items"] == 1
    assert rep["n_double_screened"] == 0
    assert rep["ready_to_screen"] == 1
    assert rep["cohen_kappa"] is None


def test_agreement_counts_only_double_screened_rows():
    queue = [
        _q("include", "include"),
        _q("exclude", "exclude"),
        _q("include", "exclude"),   # conflict
        _q("include", ""),          # single reviewer -> not a pair
        _q("", ""),                 # no decisions -> not a pair
    ]
    assert len(queue_reviewer_pairs(queue)) == 3
    rep = screening_agreement(queue)
    assert rep["n_items"] == 5
    assert rep["n_double_screened"] == 3
    assert rep["agree_total"] == 2
    assert rep["agree_include"] == 1
    assert rep["agree_exclude"] == 1
    assert rep["conflicts"] == 1
    assert rep["percent_agreement"] == round(2 / 3, 4)
    assert rep["cohen_kappa"] is not None


def test_agreement_perfect_kappa_is_one():
    queue = [_q("include", "include"), _q("exclude", "exclude"), _q("include", "include")]
    rep = screening_agreement(queue)
    assert rep["percent_agreement"] == 1.0
    assert rep["cohen_kappa"] == 1.0


def test_agreement_reports_screenability_and_export_gate():
    queue = [
        _q("include", "include", flag="ready_to_screen", export_ready=True),
        _q(flag="no_full_text"),
        _q(flag="poor_ocr"),
    ]
    rep = screening_agreement(queue)
    assert rep["ready_to_screen"] == 1
    assert rep["no_full_text"] == 1
    assert rep["poor_ocr"] == 1
    assert rep["export_ready"] == 1
