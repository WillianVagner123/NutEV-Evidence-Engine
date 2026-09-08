#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from nutev.migration import run_legacy_multitenant_dry_run
from nutev.migration.profiles import FIRST_PARTY_DOCTORATE_PROFILE, get_migration_profile


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan a reviewed legacy multi-tenant migration without mutating source or platform state.")
    parser.add_argument("--profile", default=FIRST_PARTY_DOCTORATE_PROFILE)
    parser.add_argument("--source-root", action="append", type=Path, default=[])
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--report", type=Path, default=Path("LEGACY_MIGRATION_MANIFEST.json"))
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _discover_roots(explicit: list[Path]) -> list[Path]:
    if explicit:
        return explicit
    return sorted(path for path in Path.cwd().glob("project_output*") if path.is_dir())


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.dry_run:
        print("Dry-run acknowledgement required; activation is not implemented by this command.", file=sys.stderr)
        return 2
    try:
        plan = get_migration_profile(args.profile)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    report = run_legacy_multitenant_dry_run(
        plan=plan,
        source_roots=_discover_roots(args.source_root),
        report_path=args.report,
        explicit_mapping_path=args.mapping,
    )
    print(json.dumps({
        "status": report["status"],
        "report": str(Path(args.report).expanduser().resolve()),
        "files_seen": report["counts"]["files_seen"],
        "unknown": report["counts"]["by_classification"]["UNKNOWN"],
        "blockers": report["blockers"],
        "activation_supported": report["activation_supported"],
    }, ensure_ascii=False, sort_keys=True))
    if report["status"] == "SOURCE_NOT_MATERIALIZED":
        return 3
    if report["status"] == "DRY_RUN_FAIL":
        return 4
    if report["status"] == "DRY_RUN_REVIEW_REQUIRED":
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
