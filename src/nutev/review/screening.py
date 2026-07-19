"""Two-reviewer screening flow (§13): decisions, conflict, adjudication, gate.

Pure, testable logic for JBI/PRISMA-ScR screening by two independent reviewers,
with standardized exclusion reasons, visible conflicts, adjudication, inter-rater
agreement (Cohen's kappa) and an *export gate* that blocks any record that has
not been validated (§13 last rule, §18.17).

Decisions are append-only rows (immutable history); status is always *derived*
from them, never overwritten. Nothing here decides anything by itself — it
records and reconciles what two humans decided.
"""
from __future__ import annotations

from collections import Counter

PHASES = ("title_abstract", "full_text")
SCREEN_DECISIONS = ("include", "exclude", "uncertain")

# Standardized full-text exclusion reasons (§13). Configurable/extensible.
EXCLUSION_REASONS = (
    "wrong_population",          # not adults / out-of-scope population
    "not_normative_document",   # not a guideline/normative/operational document
    "wrong_period",             # outside the target date window
    "wrong_language",           # not PT/EN/ES (or configured)
    "empirical_study",          # trial/observational/mechanism -> Article 2
    "review_or_protocol",       # narrative/systematic review or protocol only
    "duplicate",                # same asset/version already included
    "superseded_version",       # an in-force edition supersedes this one
    "no_full_text",             # full text unavailable
    "poor_ocr",                 # text too poor to assess
    "out_of_scope",             # does not address the review question
    "aggregator_or_derived",    # aggregating spreadsheet / pipeline-derived file
    "other",
)


def _latest_by_reviewer(decisions: list[dict], phase: str) -> dict[str, dict]:
    """Last decision per reviewer for a phase (append-only -> last wins)."""
    out: dict[str, dict] = {}
    for d in decisions:
        if d.get("phase") != phase:
            continue
        reviewer = str(d.get("reviewer") or "").strip()
        if reviewer:
            out[reviewer] = d
    return out


def reconcile_record(decisions: list[dict], phase: str) -> dict:
    """Reconcile one record's decisions for a phase across reviewers.

    status ∈ {needs_second_reviewer, agree_include, agree_exclude, conflict}.
    Two DISTINCT reviewers are required; 'uncertain' from either side is a
    conflict (needs adjudication), never a silent include/exclude.
    """
    by_rev = _latest_by_reviewer(decisions, phase)
    if len(by_rev) < 2:
        return {"phase": phase, "status": "needs_second_reviewer", "n_reviewers": len(by_rev)}
    labels = [str(d.get("decision") or "").lower() for d in by_rev.values()]
    if all(x == "include" for x in labels):
        status = "agree_include"
    elif all(x == "exclude" for x in labels):
        status = "agree_exclude"
    else:
        status = "conflict"
    return {"phase": phase, "status": status, "n_reviewers": len(by_rev), "labels": labels}


def adjudicate(record_id: str, phase: str, adjudicator: str, decision: str, rationale: str) -> dict:
    """Return an adjudication record resolving a conflict (append-only)."""
    if decision.lower() not in {"include", "exclude"}:
        raise ValueError("adjudication decision must be include or exclude")
    if not str(adjudicator).strip() or not str(rationale).strip():
        raise ValueError("adjudication requires an adjudicator and a rationale")
    return {
        "record_id": record_id, "phase": phase, "adjudicator": adjudicator,
        "decision": decision.lower(), "rationale": rationale, "kind": "adjudication",
    }


def cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    """Cohen's kappa for paired reviewer labels. 1.0 = perfect, 0 = chance."""
    n = len(pairs)
    if n == 0:
        return 0.0
    po = sum(1 for a, b in pairs if a == b) / n
    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    categories = set(a_counts) | set(b_counts)
    pe = sum((a_counts[c] / n) * (b_counts[c] / n) for c in categories)
    if abs(1 - pe) < 1e-12:
        return 1.0 if po == 1.0 else 0.0
    return round((po - pe) / (1 - pe), 4)


def final_decision(record_decisions: list[dict], adjudications: list[dict] | None = None) -> dict:
    """Final full-text decision for a record: agreement, else adjudication, else pending."""
    adjudications = adjudications or []
    rec = reconcile_record(record_decisions, "full_text")
    if rec["status"] == "agree_include":
        return {"decision": "include", "basis": "agreement"}
    if rec["status"] == "agree_exclude":
        return {"decision": "exclude", "basis": "agreement"}
    adj = next((a for a in adjudications if a.get("phase") == "full_text"), None)
    if adj:
        return {"decision": adj["decision"], "basis": "adjudication", "rationale": adj.get("rationale", "")}
    return {"decision": "pending", "basis": rec["status"]}


def is_export_ready(record_decisions: list[dict], adjudications: list[dict] | None = None) -> bool:
    """A record may enter scientific export ONLY if full-text screening resolved
    to include (by agreement or adjudication). Everything else is blocked."""
    return final_decision(record_decisions, adjudications).get("decision") == "include"


def export_blocked_reason(record_decisions: list[dict], adjudications: list[dict] | None = None) -> str:
    """Empty string if export-ready; otherwise a human-readable block reason."""
    fd = final_decision(record_decisions, adjudications)
    if fd["decision"] == "include":
        return ""
    if fd["decision"] == "exclude":
        return "excluded in full-text screening"
    return f"not validated ({fd['basis']})"


# --------------------------------------------------------------------------- #
# Screening queue from pipeline rows (documents awaiting two-reviewer screening).
# --------------------------------------------------------------------------- #

_FULLTEXT_OK = {"ok", "ok_ocr", "fake_pdf_html", "fake_pdf_text"}


def build_screening_queue(rows: list[dict]) -> list[dict]:
    """One screening item per document, flagging those unfit to screen yet.

    Documents with no usable full text (or failed/needs-setup OCR) are flagged
    ``no_full_text`` / ``poor_ocr`` so they go to a separate queue and cannot be
    silently included (§13 "fila de documentos sem texto").
    """
    queue: list[dict] = []
    for r in rows:
        status = str(r.get("extraction_status") or "")
        if status in _FULLTEXT_OK:
            flag = "ready_to_screen"
        elif status in {"pdf_needs_ocr_setup", "ocr_fail"}:
            flag = "poor_ocr"
        else:
            flag = "no_full_text"
        queue.append({
            "record_id": r.get("_guide_key") or r.get("name", ""),
            "name": r.get("name", ""),
            "country": r.get("country", r.get("reference_country", "")),
            "reference": r.get("reference", ""),
            "extraction_status": status,
            "screen_flag": flag,
            "phase": "title_abstract",
            "reviewer_1_decision": "",
            "reviewer_2_decision": "",
            "exclusion_reason": "",
            "status": "needs_second_reviewer",
            "export_ready": False,  # nothing is export-ready until two reviewers validate
        })
    return queue
