#!/usr/bin/env python3
"""Read-only NutEV production volume inventory (group sizes; no file contents)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil

CATEGORIES = {
    "temporary_search_results": "15_web_searches",
    "search_logs": "07_logs",
    "cached_full_text_and_pdfs": "16_search_full_text_cache",
    "bibliographic_registry": "registry",
    "scientific_artifacts": "scientific",
    "research_agent_context": "agent_context",
    "platform_accounts_workspaces": "platform",
    "review_and_validation": "16_validation_server",
    "retrieval_bank": "bank",
}


def directory_size(path: Path) -> dict:
    """Walk without following symlinks, counting bytes and files only."""
    result = {"bytes": 0, "files": 0, "directories": 0, "symlinks_skipped": 0, "errors": 0}
    if not path.is_dir() or path.is_symlink():
        return result

    def error(_error: OSError) -> None:
        result["errors"] += 1

    for folder, dirs, files in os.walk(path, topdown=True, followlinks=False, onerror=error):
        parent = Path(folder)
        kept = []
        for dirname in dirs:
            candidate = parent / dirname
            if candidate.is_symlink():
                result["symlinks_skipped"] += 1
            else:
                kept.append(dirname)
                result["directories"] += 1
        dirs[:] = kept
        for filename in files:
            candidate = parent / filename
            try:
                if candidate.is_symlink():
                    result["symlinks_skipped"] += 1
                elif candidate.is_file():
                    result["bytes"] += candidate.stat().st_size
                    result["files"] += 1
            except OSError:
                result["errors"] += 1
    return result


def inventory(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError("Output root does not exist")
    disk = shutil.disk_usage(root)
    by_category = {}
    for label, relative in CATEGORIES.items():
        by_category[label] = directory_size(root / relative)
    other_dirs = [
        path for path in root.iterdir()
        if path.is_dir() and not path.is_symlink() and path.name not in CATEGORIES.values()
    ]
    by_category["other_directories"] = {
        key: sum(directory_size(path)[key] for path in other_dirs)
        for key in ("bytes", "files", "directories", "symlinks_skipped", "errors")
    }
    return {
        "filesystem_total_bytes": disk.total,
        "filesystem_used_bytes": disk.used,
        "filesystem_free_bytes": disk.free,
        "volume_root": str(root),
        "categories": by_category,
        "warning": "This is an inventory, not evidence that a group is safe to delete.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("project_output_reference"))
    args = parser.parse_args()
    print(json.dumps(inventory(args.root), indent=2))


if __name__ == "__main__":
    main()
