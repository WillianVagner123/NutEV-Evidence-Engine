#!/usr/bin/env python3
"""Atomically refresh Article Workbench from the cumulative Article Registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nutev.registry.workbench import refresh_cumulative_workbench


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Project the cumulative NutEV Article Registry into the Article Workbench. "
            "Existing verified scientific cards, excerpts, and result bundles are preserved; "
            "the active SQLite file is switched only after integrity and hash checks pass."
        )
    )
    parser.add_argument(
        "--output-root",
        default="project_output_reference",
        help="NutEV persistent output root.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = refresh_cumulative_workbench(output_root=Path(args.output_root))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
