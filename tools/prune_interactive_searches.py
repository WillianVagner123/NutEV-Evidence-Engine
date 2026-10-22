#!/usr/bin/env python3
"""Conservatively expire temporary web-search JSON without touching scientific assets.

Report-only by default. Explicit review, exhaustive and unrecognized searches,
Registry, placements, OCR/PDF cache, and scientific volumes are always untouched.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path


def _expired_quick(payload: object, *, cutoff: datetime, expected_id: str | None = None) -> bool:
    if not isinstance(payload, dict):
        return False
    if expected_id is not None and payload.get("search_id") != expected_id:
        return False
    if payload.get("search_mode") != "interactive_bounded":
        return False
    plan = payload.get("query_plan")
    if isinstance(plan, dict) and plan.get("mode") not in (None, "", "quick"):
        return False
    try:
        created = datetime.fromisoformat(str(payload["created_at"]).replace("Z", "+00:00"))
    except (ValueError, KeyError, TypeError):
        return False
    return created.tzinfo is not None and created.astimezone(timezone.utc) < cutoff


def inventory(root: Path, *, days: int = 2, apply: bool = False) -> dict:
    if days < 1:
        raise ValueError("days must be >= 1")
    root = root.resolve()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = {
        "mode": "apply" if apply else "dry_run",
        "days": days,
        "eligible_runs": 0,
        "eligible_bytes": 0,
        "removed_runs": 0,
        "removed_bytes": 0,
        "eligible_latest_bytes": 0,
        "removed_latest_bytes": 0,
        "skipped": 0,
        "errors": [],
    }
    base = root / "15_web_searches"
    if base.is_dir() and not base.is_symlink():
        for path in base.glob("web_*/result.json"):
            folder = path.parent
            try:
                if folder.is_symlink() or path.is_symlink() or not folder.is_dir():
                    result["skipped"] += 1
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                # Both the declared timestamp and filesystem mtime must be old;
                # this prevents deleting a run being rewritten by an active worker.
                if (not _expired_quick(payload, cutoff=cutoff, expected_id=folder.name)
                        or datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) >= cutoff):
                    result["skipped"] += 1
                    continue
                # Delete only the known temporary result file, not arbitrary
                # extra files that a person or workflow might have placed here.
                size = path.stat().st_size
                result["eligible_runs"] += 1
                result["eligible_bytes"] += size
                if apply:
                    path.unlink()
                    try:
                        folder.rmdir()  # Only succeeds if genuinely empty.
                    except OSError:
                        pass
                    result["removed_runs"] += 1
                    result["removed_bytes"] += size
            except (OSError, ValueError, KeyError, TypeError) as exc:
                result["errors"].append({"run": folder.name, "error": type(exc).__name__})

    # Historical versions duplicated the last quick search as a full JSON file.
    # Retain latest.json if it is recent, review-grade, symlinked or malformed.
    latest = root / "07_logs" / "web_search" / "latest.json"
    if latest.is_file() and not latest.is_symlink():
        try:
            payload = json.loads(latest.read_text(encoding="utf-8"))
            if (_expired_quick(payload, cutoff=cutoff)
                    and datetime.fromtimestamp(latest.stat().st_mtime, timezone.utc) < cutoff):
                size = latest.stat().st_size
                result["eligible_latest_bytes"] = size
                if apply:
                    latest.unlink()
                    result["removed_latest_bytes"] = size
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result["errors"].append({"run": "latest.json", "error": type(exc).__name__})
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
