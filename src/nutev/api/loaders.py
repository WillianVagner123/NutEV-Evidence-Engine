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


def tail_jsonl(path: Path, limit: int, offset: int) -> dict:
    """Tail a JSONL event log for live monitoring.

    ``offset<=0`` (or beyond EOF — i.e. a fresh run rotated the file) returns the
    last ``limit`` events. A positive ``offset`` is a *count of already-seen
    events*: it returns the events after the first ``offset`` lines
    (``lines[offset:]``), so a client polls with ``?offset=<previous total>`` to
    stream only what is new. ``total`` is the current line count = the next cursor.
    """
    safe_limit = max(1, min(int(limit), MAX_PAGE_LIMIT))
    if not path.exists():
        return {"available": False, "total": 0, "offset": 0, "items": []}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return {"available": False, "total": 0, "offset": 0, "items": []}
    total = len(lines)
    off = int(offset)
    chunk = lines[off : off + safe_limit] if 0 < off <= total else lines[max(0, total - safe_limit):]
    items: list[dict] = []
    for line in chunk:
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except Exception:
            continue
    last = items[-1] if items else {}
    return {
        "available": total > 0,
        "total": total,
        "offset": off,
        "run_id": last.get("run_id"),
        "last_event_at": last.get("event_at"),
        "last_stage": last.get("stage"),
        "items": items,
    }


def summarize_run_events(path: Path) -> dict:
    """Live progress from the event log: counts per stage + results returned so
    far. Lets the UI show a running tally before run_summary.json exists (which is
    only written when the pipeline finishes)."""
    if not path.exists():
        return {"available": False, "total": 0, "stages": {}, "rows_returned": 0, "rows_found": 0, "last_stage": None, "download": None}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return {"available": False, "total": 0, "stages": {}, "rows_returned": 0, "rows_found": 0, "last_stage": None, "download": None}
    stages: dict[str, int] = {}
    rows_returned = 0
    rows_found = 0
    last_stage = None
    download = None  # latest full-text download position {done,total}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        stage = ev.get("stage") or ev.get("event_kind") or "?"
        stages[stage] = stages.get(stage, 0) + 1
        last_stage = stage
        meta = ev.get("meta_json") or {}
        tr, tf = meta.get("total_returned"), meta.get("total_found")
        if isinstance(tr, (int, float)) and not isinstance(tr, bool):
            rows_returned += int(tr)
        if isinstance(tf, (int, float)) and not isinstance(tf, bool):
            rows_found += int(tf)
        if stage in ("download_started", "download_progress"):
            t = meta.get("total")
            d = meta.get("done", 0)
            if isinstance(t, (int, float)) and not isinstance(t, bool):
                download = {"done": int(d) if isinstance(d, (int, float)) and not isinstance(d, bool) else 0, "total": int(t)}
        elif stage == "download_completed":
            download = None
    return {
        "available": len(stages) > 0,
        "total": sum(stages.values()),
        "stages": stages,
        "rows_returned": rows_returned,
        "rows_found": rows_found,
        "last_stage": last_stage,
        "download": download,
    }


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
