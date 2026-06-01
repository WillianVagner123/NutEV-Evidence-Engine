from __future__ import annotations

from pathlib import Path
import json
import math
import re
import pandas as pd

EXCEL_CELL_LIMIT = 32767

try:
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
except Exception:
    ILLEGAL_CHARACTERS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")

EXTRA_BAD_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\uFFFE\uFFFF]")
SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")


def _sanitize_excel_value(value):
    if value is None:
        return ""

    if isinstance(value, float) and math.isnan(value):
        return ""

    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    elif isinstance(value, (list, dict, tuple, set)):
        try:
            value = json.dumps(value, ensure_ascii=False)
        except Exception:
            value = str(value)
    elif not isinstance(value, (str, int, float, bool)):
        value = str(value)

    if isinstance(value, str):
        value = value.replace("\r\n", "\n").replace("\r", "\n")
        value = ILLEGAL_CHARACTERS_RE.sub(" ", value)
        value = EXTRA_BAD_RE.sub(" ", value)
        value = SURROGATE_RE.sub("", value)
        value = value.replace("\x00", " ")
        value = value.encode("utf-8", "ignore").decode("utf-8", "ignore")
        value = value.strip()
        if len(value) > EXCEL_CELL_LIMIT:
            value = value[: EXCEL_CELL_LIMIT - 20] + " [TRUNCATED]"
    return value


def sanitize_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(_sanitize_excel_value)
    out.columns = [_sanitize_excel_value(c) for c in out.columns]
    return out


def write_analysis_xlsx(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = sanitize_dataframe_for_excel(pd.DataFrame(rows))
    try:
        df.to_excel(path, index=False)
    except Exception:
        df.to_csv(path.with_suffix(".csv"), index=False, encoding="utf-8-sig")
        path.touch()


def write_excel_sheet(writer, df: pd.DataFrame, sheet_name: str) -> None:
    safe_df = sanitize_dataframe_for_excel(df)
    safe_df.to_excel(writer, sheet_name=str(sheet_name)[:31], index=False)


def write_excel_file(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_df = sanitize_dataframe_for_excel(df)
    try:
        safe_df.to_excel(path, index=False)
    except Exception:
        safe_df.to_csv(path.with_suffix(".csv"), index=False, encoding="utf-8-sig")
        path.touch()