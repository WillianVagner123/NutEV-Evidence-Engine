from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

LANES = [
    "unscreened",
    "include",
    "exclude",
    "maybe",
    "conflict",
    "needs_more_evidence",
    "adjudication",
    "protocol_ready",
]

DECISION_TO_LANE = {
    "approve": "include",
    "approve_with_revision": "maybe",
    "reject": "exclude",
    "needs_more_evidence": "needs_more_evidence",
    "needs_second_reviewer": "adjudication",
    "conflict": "conflict",
    "not_applicable": "exclude",
}

FINAL_TO_LANE = {
    "approved": "protocol_ready",
    "revised": "maybe",
    "rejected": "exclude",
    "insufficient_evidence": "needs_more_evidence",
    "conflicting_evidence": "conflict",
    "pending": "unscreened",
}


def _str(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return "" if text.lower() == "nan" else text


def infer_item_id(row: pd.Series | dict[str, Any]) -> str:
    data = dict(row)
    for key in ["item_id", "claim_id", "recommendation_id", "document_id", "record_id"]:
        value = _str(data.get(key))
        if value:
            return value
    return ""


def infer_item_type(row: pd.Series | dict[str, Any]) -> str:
    data = dict(row)
    if _str(data.get("item_type")):
        return _str(data.get("item_type"))
    if _str(data.get("claim_id")):
        return "claim"
    if _str(data.get("recommendation_id")):
        return "recommendation_candidate"
    if _str(data.get("document_id")):
        return "metadata_only_record"
    return "review_item"


def infer_item_title(row: pd.Series | dict[str, Any]) -> str:
    data = dict(row)
    for key in ["title", "recommendation_text", "claim_text", "document_title", "source_title"]:
        value = _str(data.get(key))
        if value:
            return value[:180]
    item_id = infer_item_id(data)
    return item_id or "Untitled review item"


def build_review_queue(claims: pd.DataFrame, recommendations: pd.DataFrame, explicit_queue: pd.DataFrame | None = None) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    if explicit_queue is not None and not explicit_queue.empty:
        q = explicit_queue.copy()
        q["item_type"] = q.apply(infer_item_type, axis=1)
        q["item_id"] = q.apply(infer_item_id, axis=1)
        frames.append(q)
    if not claims.empty:
        c = claims.copy()
        needs = pd.Series(False, index=c.index)
        if "needs_human_review" in c.columns:
            needs = c["needs_human_review"].astype(str).str.lower().isin(["true", "1", "yes", "sim"])
        if "claim_status" in c.columns:
            needs = needs | c["claim_status"].astype(str).isin(["inference_only", "insufficient_evidence", "conflicting", "needs_human_review"])
        add = c[needs].copy()
        if not add.empty:
            add["item_type"] = "claim"
            add["item_id"] = add.apply(infer_item_id, axis=1)
            frames.append(add)
    if not recommendations.empty and "recommendation_status" in recommendations.columns:
        r = recommendations.copy()
        status = r["recommendation_status"].astype(str)
        needs = status.isin(["insufficient_evidence", "conflicting_evidence", "draft_needs_evidence", "ready_for_human_review"])
        add_r = r[needs].copy()
        if not add_r.empty:
            add_r["item_type"] = "recommendation_candidate"
            add_r["item_id"] = add_r.apply(infer_item_id, axis=1)
            frames.append(add_r)
    if not frames:
        return pd.DataFrame(columns=["item_id", "item_type", "title", "review_lane"])
    queue = pd.concat(frames, ignore_index=True)
    queue["item_id"] = queue.apply(infer_item_id, axis=1)
    queue["item_type"] = queue.apply(infer_item_type, axis=1)
    queue["title"] = queue.apply(infer_item_title, axis=1)
    queue = queue[queue["item_id"].astype(str) != ""].drop_duplicates(subset=["item_type", "item_id"], keep="first")
    queue["review_lane"] = "unscreened"
    return queue


def apply_latest_decisions(queue: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    if queue.empty:
        return queue.copy()
    out = queue.copy()
    out["review_lane"] = out.get("review_lane", "unscreened")
    if decisions.empty or "item_id" not in decisions.columns:
        return out
    latest = decisions.copy()
    if "created_at" in latest.columns:
        latest = latest.sort_values("created_at")
    latest = latest.drop_duplicates(subset=["item_id"], keep="last")
    cols = ["item_id", "reviewer_name", "reviewer_role", "reviewer_decision", "reviewer_notes", "final_decision", "decision_date", "created_at"]
    merged = out.merge(latest[[c for c in cols if c in latest.columns]], on="item_id", how="left")
    def lane(row: pd.Series) -> str:
        final = _str(row.get("final_decision"))
        decision = _str(row.get("reviewer_decision"))
        if final in FINAL_TO_LANE and final != "pending":
            return FINAL_TO_LANE[final]
        if decision in DECISION_TO_LANE:
            return DECISION_TO_LANE[decision]
        status = _str(row.get("recommendation_status")) or _str(row.get("claim_status"))
        if "conflict" in status:
            return "conflict"
        if "insufficient" in status or "needs" in status or "draft" in status:
            return "needs_more_evidence"
        return "unscreened"
    merged["review_lane"] = merged.apply(lane, axis=1)
    return merged


def build_review_workspace(claims: pd.DataFrame, recommendations: pd.DataFrame, decisions: pd.DataFrame, explicit_queue: pd.DataFrame | None = None) -> pd.DataFrame:
    queue = build_review_queue(claims, recommendations, explicit_queue)
    return apply_latest_decisions(queue, decisions)


def lane_counts(workspace: pd.DataFrame) -> pd.DataFrame:
    if workspace.empty or "review_lane" not in workspace.columns:
        return pd.DataFrame({"review_lane": LANES, "count": [0 for _ in LANES]})
    counts = workspace["review_lane"].astype(str).value_counts().to_dict()
    return pd.DataFrame({"review_lane": LANES, "count": [int(counts.get(lane, 0)) for lane in LANES]})


def export_review_workspace(project_root: Path, workspace: pd.DataFrame) -> Path:
    out_dir = project_root / "06_tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "NUTEV_REVIEW_WORKSPACE.csv"
    workspace.to_csv(path, index=False)
    return path
