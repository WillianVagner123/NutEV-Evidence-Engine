from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import uuid

import pandas as pd

REQUIRED_FIELDS = [
    "decision_id",
    "item_type",
    "item_id",
    "reviewer_name",
    "reviewer_role",
    "reviewer_decision",
    "reviewer_notes",
    "final_decision",
    "decision_date",
    "created_at",
]

ITEM_TYPES = {"claim", "recommendation_candidate", "conflict", "metadata_only_record", "unsupported_claim"}
REVIEWER_ROLES = {"principal_investigator", "advisor", "coadvisor", "reviewer_1", "reviewer_2", "external_reviewer"}
REVIEWER_DECISIONS = {"approve", "approve_with_revision", "reject", "needs_more_evidence", "needs_second_reviewer", "conflict", "not_applicable"}
FINAL_DECISIONS = {"pending", "approved", "revised", "rejected", "insufficient_evidence", "conflicting_evidence"}


def _path(project_root: Path) -> Path:
    return project_root / "07_logs" / "human_review_decisions.csv"


def load_human_review_decisions(project_root: Path) -> pd.DataFrame:
    p = _path(project_root)
    if not p.exists():
        return pd.DataFrame(columns=REQUIRED_FIELDS)
    try:
        return pd.read_csv(p)
    except Exception:
        return pd.DataFrame(columns=REQUIRED_FIELDS)


def validate_human_review_decision(decision: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    out = dict(decision)
    out.setdefault("decision_id", f"hrd_{uuid.uuid4().hex[:12]}")
    out.setdefault("reviewer_notes", "")
    out.setdefault("decision_date", now[:10])
    out.setdefault("created_at", now)

    for k in REQUIRED_FIELDS:
        if k not in out:
            raise ValueError(f"missing field: {k}")
    if out["item_type"] not in ITEM_TYPES:
        raise ValueError("invalid item_type")
    if out["reviewer_role"] not in REVIEWER_ROLES:
        raise ValueError("invalid reviewer_role")
    if out["reviewer_decision"] not in REVIEWER_DECISIONS:
        raise ValueError("invalid reviewer_decision")
    if out["final_decision"] not in FINAL_DECISIONS:
        raise ValueError("invalid final_decision")
    return out


def append_human_review_decision(project_root: Path, decision: dict) -> None:
    valid = validate_human_review_decision(decision)
    p = _path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    old = load_human_review_decisions(project_root)
    combined = pd.concat([old, pd.DataFrame([valid])], ignore_index=True)
    combined.to_csv(p, index=False)


def merge_human_review_decisions(queue_df: pd.DataFrame, decisions_df: pd.DataFrame) -> pd.DataFrame:
    if queue_df.empty:
        return decisions_df.copy()
    if decisions_df.empty:
        return queue_df.copy()
    q = queue_df.copy()
    if "item_id" not in q.columns:
        q["item_id"] = q.get("claim_id", q.get("recommendation_id", ""))
    # Sort by parsed timestamp (not lexically) so "latest decision wins" stays
    # correct even if a row uses a different created_at format; unparseable
    # values become NaT and sort first, never overriding a real decision.
    latest = decisions_df.copy()
    if "created_at" in latest.columns:
        latest = (
            latest.assign(_created_at_dt=pd.to_datetime(latest["created_at"], utc=True, errors="coerce"))
            .sort_values("_created_at_dt")
            .drop(columns="_created_at_dt")
        )
    latest = latest.drop_duplicates(subset=["item_id"], keep="last")
    cols = ["item_id", "reviewer_name", "reviewer_role", "reviewer_decision", "reviewer_notes", "final_decision", "decision_date"]
    return q.merge(latest[[c for c in cols if c in latest.columns]], on="item_id", how="left")
