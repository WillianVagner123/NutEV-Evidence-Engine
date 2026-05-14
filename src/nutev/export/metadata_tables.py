from __future__ import annotations
import csv
from pathlib import Path

def write_metadata_csv(rows: list[dict], path: Path) -> None:
    if not rows: return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for r in rows for k in r.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)

def write_simple_csv(rows: list[dict], path: Path) -> None:
    write_metadata_csv(rows, path)
