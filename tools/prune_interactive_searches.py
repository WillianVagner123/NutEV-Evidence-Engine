#!/usr/bin/env python3
"""Bounded, opt-in cleanup of expired interactive search JSON snapshots.

Never touches registry, scientific, Article 1/2, full-text cache, Docker volumes,
or any run in structured/exact review mode. Defaults to report-only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil

def inventory(root: Path, *, days: int = 2, apply: bool = False) -> dict:
    if days < 1:
        raise ValueError("days must be >= 1")
    base = (root.resolve() / "15_web_searches")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = {"mode": "apply" if apply else "dry_run", "days": days,
              "eligible_runs": 0, "eligible_bytes": 0, "removed_runs": 0,
              "removed_bytes": 0, "skipped": 0, "errors": []}
    if not base.is_dir():
        return result
    for path in base.glob("web_*/result.json"):
        folder = path.parent
        try:
            if folder.is_symlink() or path.is_symlink() or not folder.is_dir():
                result["skipped"] += 1
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("search_id") != folder.name:
                result["skipped"] += 1
                continue
            # Never expire review/audit-grade, exhaustive or explicit research runs.
            if payload.get("search_mode") != "interactive_bounded":
                result["skipped"] += 1
                continue
            if isinstance(payload.get("query_plan"), dict) and payload["query_plan"].get("mode") not in (None, "", "quick"):
                result["skipped"] += 1
                continue
            created = datetime.fromisoformat(str(payload["created_at"]).replace("Z","+00:00"))
            if created.tzinfo is None or created.astimezone(timezone.utc) >= cutoff:
                result["skipped"] += 1
                continue
            files = list(folder.rglob("*"))
            if any(p.is_symlink() for p in files):
                result["skipped"] += 1
                continue
            size = sum(p.stat().st_size for p in files if p.is_file())
            result["eligible_runs"] += 1
            result["eligible_bytes"] += size
            if apply:
                shutil.rmtree(folder)
                result["removed_runs"] += 1
                result["removed_bytes"] += size
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            result["errors"].append({"run": folder.name, "error": type(exc).__name__})
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("project_output_reference"))
    parser.add_argument("--days", type=int, default=2)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(inventory(args.root, days=args.days, apply=args.apply), indent=2))

if __name__ == "__main__":
    main()
