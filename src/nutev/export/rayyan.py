from __future__ import annotations
import csv
from pathlib import Path

def write_rayyan(rows: list[dict], path: Path) -> None:
    cols=["title","url","source","workstream","relevance_score"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c:r.get(c,"") for c in cols})
