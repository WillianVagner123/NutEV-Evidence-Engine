#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from nutev.registry.history_migration import run_history_migration_dry_run


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Rehearse historical NutEV Article Registry migration against a disposable "
            "SQLite registry. This command never mutates the real Registry or legacy files."
        )
    )
    parser.add_argument(
        "--source-root",
        action="append",
        type=Path,
        default=[],
        help=(
            "Legacy project_output root. Repeat for multiple roots. When omitted, "
            "existing ./project_output* directories are discovered."
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("REGISTRY_MIGRATION_REPORT.json"),
        help="Destination for the dry-run report.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required safety acknowledgement. Apply mode is intentionally unavailable.",
    )
    return parser


def _discover_roots(explicit: list[Path]) -> list[Path]:
    if explicit:
        return explicit
    return sorted(path for path in Path.cwd().glob("project_output*") if path.is_dir())


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.dry_run:
        print(
            "Refusing to continue: this PR supports --dry-run only. "
            "Apply/cutover requires a reviewed REGISTRY_MIGRATION_REPORT.json.",
            file=sys.stderr,
        )
        return 2

    roots = _discover_roots(args.source_root)
    report = run_history_migration_dry_run(
        source_roots=roots,
        report_path=args.report,
    )
    print(json.dumps({
        "status": report["status"],
        "report": str(args.report),
        "records_seen": report["records_seen"],
        "unique_articles_created": report["unique_articles_created"],
        "identity_conflicts": report["identity_conflicts"],
        "quarantined_records": report["quarantined_records"],
    }, ensure_ascii=False, sort_keys=True))

    if report["status"] == "SOURCE_NOT_MATERIALIZED":
        return 3
    if report["status"] == "DRY_RUN_FAIL":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
