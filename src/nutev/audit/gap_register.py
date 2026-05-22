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


def build_evidence_gap_register(claims: list[Any], recommendations: list[Any], conflicts: list[dict[str, Any]] | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    conflicts = conflicts or []
    for rec in recommendations:
        r = _as_dict(rec)
        support = _listish(r.get("supporting_claim_ids"))
        conflicting = _listish(r.get("conflicting_claim_ids"))
        if not support:
            rows.append({
                "gap_id": f"gap_{r.get('recommendation_id', 'unknown')}_support",
                "domain": ",".join(_listish(r.get("nutev_domains"))) or "unspecified",
                "protocol_component": r.get("protocol_component", "unspecified"),
                "clinical_condition": ",".join(_listish(r.get("clinical_conditions"))),
                "dietary_pattern": ",".join(_listish(r.get("dietary_patterns"))),
                "missing_evidence_type": "supporting_claims",
                "reason": "Recommendation candidate has no supporting_claim_ids.",
                "detected_from": r.get("recommendation_id"),
                "priority": "high",
                "suggested_next_search": "Search for guideline, review or intervention evidence supporting this protocol component.",
                "human_notes": "",
            })
        if conflicting:
            rows.append({
                "gap_id": f"gap_{r.get('recommendation_id', 'unknown')}_conflict",
                "domain": ",".join(_listish(r.get("nutev_domains"))) or "unspecified",
                "protocol_component": r.get("protocol_component", "unspecified"),
                "clinical_condition": ",".join(_listish(r.get("clinical_conditions"))),
                "dietary_pattern": ",".join(_listish(r.get("dietary_patterns"))),
                "missing_evidence_type": "adjudication",
                "reason": "Recommendation candidate has conflicting_claim_ids.",
                "detected_from": r.get("recommendation_id"),
                "priority": "high",
                "suggested_next_search": "Adjudicate conflict and search for higher-quality evidence.",
                "human_notes": "",
            })
    for claim in claims:
        c = _as_dict(claim)
        if c.get("claim_status") in {"inference_only", "insufficient_evidence"} or not c.get("exact_quote"):
            rows.append({
                "gap_id": f"gap_{c.get('claim_id', 'unknown')}",
                "domain": ",".join(_listish(c.get("nutev_domains"))) or "unspecified",
                "protocol_component": ",".join(_listish(c.get("protocol_components"))) or "unspecified",
                "clinical_condition": ",".join(_listish(c.get("clinical_conditions"))),
                "dietary_pattern": ",".join(_listish(c.get("dietary_patterns"))),
                "missing_evidence_type": "exact_quote_or_validation",
                "reason": "Claim requires quote, additional evidence or human validation.",
                "detected_from": c.get("claim_id"),
                "priority": "moderate",
                "suggested_next_search": "Locate full text or corroborating evidence.",
                "human_notes": "",
            })
    for idx, conflict in enumerate(conflicts):
        rows.append({
            "gap_id": f"gap_conflict_{idx + 1}",
            "domain": ",".join(_listish(conflict.get("domains"))) or "unspecified",
            "protocol_component": "unspecified",
            "clinical_condition": "",
            "dietary_pattern": "",
            "missing_evidence_type": "conflict_resolution",
            "reason": "Possible conflict detected between claims.",
            "detected_from": f"{conflict.get('claim_id_a')}|{conflict.get('claim_id_b')}",
            "priority": "high",
            "suggested_next_search": "Prioritize adjudication and higher-quality sources.",
            "human_notes": "",
        })
    return pd.DataFrame(rows)


def export_evidence_gap_register(claims: list[Any], recommendations: list[Any], conflicts: list[dict[str, Any]] | None, tables_dir: Path) -> int:
    df = build_evidence_gap_register(claims, recommendations, conflicts)
    write_excel_file(df, tables_dir / "NUTEV_EVIDENCE_GAP_REGISTER.xlsx")
    return int(len(df))
