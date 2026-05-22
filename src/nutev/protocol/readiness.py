from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from nutev.export.excel_writer import write_excel_file


def _listish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v)]
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    if text.startswith("[") and text.endswith("]"):
        return [x.strip().strip("'\"") for x in text.strip("[]").split(",") if x.strip()]
    return [x.strip() for x in text.replace(";", ",").split(",") if x.strip()]


def _as_dict(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return dict(item)


def calculate_protocol_readiness(candidate: Any, claims: list[Any] | None = None, reviews: Any | None = None, quality_rules: dict | None = None) -> dict[str, Any]:
    c = _as_dict(candidate)
    support = _listish(c.get("supporting_claim_ids"))
    docs = _listish(c.get("supporting_document_ids"))
    lenses = _listish(c.get("evidence_lenses"))
    conflicts = _listish(c.get("conflicting_claim_ids"))
    human_status = str(c.get("human_approval_status") or "not_reviewed")
    status = str(c.get("recommendation_status") or "draft_needs_evidence")
    blockers: list[str] = []
    if not support:
        blockers.append("missing_supporting_claims")
    if conflicts or status == "conflicting_evidence":
        blockers.append("unadjudicated_conflict")
    if human_status != "approved":
        blockers.append("human_review_not_approved")
    if status in {"insufficient_evidence", "draft_needs_evidence"}:
        blockers.append(status)
    score = 0
    score += min(30, len(support) * 10)
    score += min(25, len(docs) * 8)
    score += min(20, len(lenses) * 10)
    if human_status == "approved":
        score += 25
    if conflicts:
        score -= 30
    score = max(0, min(100, score))
    if not blockers and score >= 70:
        readiness_class = "protocol_ready"
        next_action = "lock_for_protocol_consideration"
    elif "unadjudicated_conflict" in blockers:
        readiness_class = "needs_adjudication"
        next_action = "send_to_adjudication"
    elif "missing_supporting_claims" in blockers:
        readiness_class = "needs_more_evidence"
        next_action = "search_or_link_supporting_claims"
    elif "human_review_not_approved" in blockers:
        readiness_class = "needs_human_review"
        next_action = "human_review"
    else:
        readiness_class = "insufficient_evidence"
        next_action = "do_not_enter_protocol"
    return {
        "recommendation_id": c.get("recommendation_id"),
        "protocol_component": c.get("protocol_component"),
        "supporting_claims_count": len(support),
        "supporting_documents_count": len(docs),
        "evidence_lenses_count": len(lenses),
        "recommendation_status": status,
        "human_review_status": human_status,
        "conflict_status": "conflict" if conflicts else "none",
        "adjudication_status": "pending" if conflicts else "not_required",
        "readiness_score": score,
        "readiness_class": readiness_class,
        "blockers": ",".join(blockers),
        "next_action": next_action,
    }


def build_protocol_readiness_matrix(recommendations: list[Any], claims: list[Any] | None = None, reviews: Any | None = None, quality_rules: dict | None = None) -> pd.DataFrame:
    return pd.DataFrame([calculate_protocol_readiness(r, claims or [], reviews, quality_rules) for r in recommendations])


def export_protocol_readiness_matrix(recommendations: list[Any], claims: list[Any] | None, tables_dir: Path) -> int:
    df = build_protocol_readiness_matrix(recommendations, claims or [])
    write_excel_file(df, tables_dir / "NUTEV_PROTOCOL_READINESS_MATRIX.xlsx")
    return int((df.get("readiness_class", pd.Series(dtype=str)) == "protocol_ready").sum()) if not df.empty else 0
