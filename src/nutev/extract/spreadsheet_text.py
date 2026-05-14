from __future__ import annotations
from pathlib import Path
import csv

def extract_csv_text(path: Path) -> tuple[str, list[list[str]]]:
    rows=[]
    with path.open("r",encoding="utf-8",errors="ignore") as f:
        for row in csv.reader(f): rows.append(row)
    txt = "\n".join(" | ".join(c for c in r) for r in rows)
    return txt, rows

def extract_sheet_text(path: Path) -> tuple[str, list[list[str]]]:
    import openpyxl
    wb=openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows=[]
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            rows.append(["" if v is None else str(v) for v in r])
    txt="\n".join(" | ".join(r) for r in rows)
    return txt, rows
