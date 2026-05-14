from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_artifact_manifest(files: list[dict], out_path: Path) -> list[dict]:
    rows = []
    for i, item in enumerate(files, 1):
        p = Path(item["path"])
        if not p.exists():
            continue
        rows.append({
            "artifact_id": f"art_{i:05d}",
            "document_id": item.get("document_id", ""),
            "artifact_type": item.get("artifact_type", ""),
            "path": str(p),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "bytes": p.stat().st_size,
            "sha256": _sha256(p),
            "source_stage": item.get("source_stage", ""),
            "status": item.get("status", "ok"),
        })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["artifact_id", "document_id", "artifact_type", "path", "created_at", "bytes", "sha256", "source_stage", "status"])
        w.writeheader()
        w.writerows(rows)
    return rows
