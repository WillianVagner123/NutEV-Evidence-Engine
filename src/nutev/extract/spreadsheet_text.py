from __future__ import annotations

import csv
from pathlib import Path


def extract_csv_text(path: Path) -> tuple[str, list[list[str]]]:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as file_obj:
        for row in csv.reader(file_obj):
            rows.append(list(row))
    text = "\n".join(" | ".join(cell for cell in row) for row in rows)
    return text, rows


def extract_sheet_text(path: Path) -> tuple[str, list[list[str]]]:
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows: list[list[str]] = []
    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows(values_only=True):
            rows.append(["" if value is None else str(value) for value in row])
    text = "\n".join(" | ".join(row) for row in rows)
    return text, rows
