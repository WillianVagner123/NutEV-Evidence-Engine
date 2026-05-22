from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from nutev.export.excel_writer import write_excel_sheet, write_excel_file


def _as_dict(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return dict(item)


def build_locked_protocol_items(recommendations: list[Any], readiness_rows: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    recs = pd.DataFrame([_as_dict(r) for r in recommendations])
    if recs.empty:
        recs = pd.DataFrame(columns=["recommendation_id", "recommendation_status", "human_approval_status"])
    readiness = readiness_rows.copy() if readiness_rows is not None else pd.DataFrame()
    if not readiness.empty and "recommendation_id" in recs.columns:
        merged = recs.merge(readiness, on="recommendation_id", how="left", suffixes=("", "_readiness"))
    else:
        merged = recs.copy()
        if "readiness_class" not in merged.columns:
            merged["readiness_class"] = "not_assessed"
    approved = merged.get("human_approval_status", pd.Series(dtype=str)).astype(str) == "approved"
    ready = merged.get("readiness_class", pd.Series(dtype=str)).astype(str) == "protocol_ready"
    protocol_ready = merged[approved & ready].copy()
    locked = protocol_ready.copy()
    if not locked.empty:
        locked["locked_for_protocol"] = True
        locked["lock_reason"] = "approved_and_protocol_ready"
    blocked = merged[~(approved & ready)].copy()
    return {"locked_recommendations": locked, "protocol_ready_items": protocol_ready, "blocked_items": blocked}


def export_locked_protocol_items(recommendations: list[Any], readiness_rows: pd.DataFrame | None, tables_dir: Path) -> int:
    tables = build_locked_protocol_items(recommendations, readiness_rows)
    path = tables_dir / "NUTEV_LOCKED_PROTOCOL_ITEMS.xlsx"
    try:
        with pd.ExcelWriter(path) as writer:
            for name, df in tables.items():
                write_excel_sheet(writer, df, name[:31])
    except Exception:
        for name, df in tables.items():
            write_excel_file(df, tables_dir / f"NUTEV_LOCKED_PROTOCOL_ITEMS_{name}.xlsx")
    return int(len(tables.get("protocol_ready_items", pd.DataFrame())))
