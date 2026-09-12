"""Conservative hygiene for NutEV release-recovery directories.

Only canonical deploy directories that are provably incomplete are removed.
Complete snapshots and suspicious/corrupt-looking directories are preserved for
manual review. Scientific output volumes are never touched by this tool.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil

RECOVERY_NAME = re.compile(r"^[0-9a-f]{40}\.[A-Za-z0-9_-]{6,}$")


def _regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _complete_snapshot(directory: Path) -> bool | None:
    """Return True for a valid complete recovery, False for missing markers.

    Return None when both markers exist but cannot be trusted/parsed; callers
    preserve these directories rather than deleting potentially useful evidence.
    """
    manifest = directory / "volume" / "manifest.json"
    proof = directory / "volume" / "restore-proof.json"
    if not _regular_file(manifest) or not _regular_file(proof):
        return False
    try:
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        proof_data = json.loads(proof.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if (
        manifest_data.get("type") == "NUTEV_QUIESCED_SNAPSHOT"
        and manifest_data.get("version") == 2
        and proof_data.get("status") == "PASS"
        and proof_data.get("production_overwritten") is False
    ):
        return True
    return None


def prune_incomplete(base: Path, *, exclude: Path | None = None) -> dict:
    base.mkdir(parents=True, exist_ok=True)
    if base.is_symlink() or not base.is_dir():
        raise ValueError("recovery base must be a real directory")
    base_resolved = base.resolve()
    excluded = exclude.resolve() if exclude is not None else None
    if excluded is not None and excluded.parent != base_resolved:
        raise ValueError("excluded recovery directory must be inside recovery base")

    pruned = 0
    preserved_complete = 0
    preserved_suspicious = 0
    skipped_unknown = 0

    for entry in sorted(base.iterdir(), key=lambda item: item.name):
        if entry.is_symlink() or not entry.is_dir():
            skipped_unknown += 1
            continue
        resolved = entry.resolve()
        if resolved.parent != base_resolved:
            skipped_unknown += 1
            continue
        if excluded is not None and resolved == excluded:
            continue
        if not RECOVERY_NAME.fullmatch(entry.name):
            skipped_unknown += 1
            continue

        state = _complete_snapshot(entry)
        if state is True:
            preserved_complete += 1
            continue
        if state is None:
            preserved_suspicious += 1
            continue

        shutil.rmtree(entry)
        pruned += 1

    return {
        "record_type": "NUTEV_RELEASE_RECOVERY_HYGIENE",
        "schema_version": 1,
        "status": "PASS",
        "pruned_incomplete": pruned,
        "preserved_complete": preserved_complete,
        "preserved_suspicious": preserved_suspicious,
        "skipped_unknown": skipped_unknown,
        "scientific_data_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--exclude", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = prune_incomplete(args.base, exclude=args.exclude)
    except (OSError, ValueError) as exc:
        report = {
            "record_type": "NUTEV_RELEASE_RECOVERY_HYGIENE",
            "schema_version": 1,
            "status": "FAIL",
            "reason": str(exc),
            "scientific_data_modified": False,
        }
    print(json.dumps(report, sort_keys=True, indent=2 if args.json else None))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
