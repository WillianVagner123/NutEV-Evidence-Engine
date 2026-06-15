from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import pandas as pd

MAX_PAGE_LIMIT = 1000


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def read_xlsx_safe(path: Path, sheet_name: str | int | None = 0) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        data = pd.read_excel(path, sheet_name=sheet_name)
        if isinstance(data, dict):
            return next(iter(data.values())) if data else pd.DataFrame()
        return data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()


def read_json_safe(path: Path) -> dict:
    if not path.exists():
        return {"available": False, "message": f"{path.name} not found"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"available": False, "message": str(e)}


def read_markdown_safe(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def filter_df(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df.copy()
    for col, val in filters.items():
        if val is None or val == "" or col not in out.columns:
            continue
        out = out[out[col].astype(str).str.contains(str(val), case=False, na=False)]
    return out


def paginate_df(df: pd.DataFrame, limit: int, offset: int) -> dict:
    total = int(len(df))
    # Clamp so a negative offset can't select a wrong tail page and an
    # oversized limit can't serialize the whole frame into one response.
    safe_limit = max(1, min(int(limit), MAX_PAGE_LIMIT))
    safe_offset = max(0, int(offset))
    page = df.iloc[safe_offset : safe_offset + safe_limit] if total else df
    return {"available": total > 0, "total": total, "limit": safe_limit, "offset": safe_offset, "items": page.fillna("").to_dict("records")}


def list_artifacts(project_root: Path) -> list[dict]:
    patterns = [("02_metadata", "*.csv"), ("06_tables", "*.xlsx"), ("07_logs", "*.json"), ("08_docs", "*.md")]
    out = []
    for folder, globp in patterns:
        base = project_root / folder
        if not base.exists():
            continue
        for p in base.glob(globp):
            st = p.stat()
            out.append({"file_name": p.name, "relative_path": str(p.relative_to(project_root)), "size_bytes": int(st.st_size), "modified_at": datetime.fromtimestamp(st.st_mtime).isoformat(), "artifact_type": folder})
    return sorted(out, key=lambda x: x["relative_path"])
