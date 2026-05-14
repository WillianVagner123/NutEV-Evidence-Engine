from __future__ import annotations
from pathlib import Path
import json
import math
import re
import pandas as pd

EXCEL_CELL_LIMIT = 32767
CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def _sanitize_excel_value(value):
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, (list, dict, tuple, set)):
        try:
            value = json.dumps(value, ensure_ascii=False)
        except Exception:
            value = str(value)
    elif not isinstance(value, (str, int, float, bool)):
        value = str(value)

    if isinstance(value, str):
        value = value.replace("\x00", " ")
        value = CONTROL_RE.sub(" ", value)
        value = value.replace("\uFFFD", " ")
        value = value.strip()
        if len(value) > EXCEL_CELL_LIMIT:
            value = value[:EXCEL_CELL_LIMIT - 20] + " [TRUNCATED]"
    return value


def sanitize_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(_sanitize_excel_value)
    return out


def write_analysis_xlsx(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df = sanitize_dataframe_for_excel(df)
    df.to_excel(path, index=False)


def write_excel_sheet(writer, df: pd.DataFrame, sheet_name: str) -> None:
    safe_df = sanitize_dataframe_for_excel(df)
    safe_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)


def write_excel_file(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_df = sanitize_dataframe_for_excel(df)
    safe_df.to_excel(path, index=False)