#!/usr/bin/env python3
"""Materialize the empty NutEV platform schema for pilot runtime startup.

This command is intentionally infrastructure-only. It never provisions users,
workspaces, projects, applications, searches, legacy bindings, or scientific
state.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from nutev.tenancy import initialize_platform_database


def _default_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path("/app/project_output_reference/platform/auth.sqlite3")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=_default_database())
    args = parser.parse_args()
    tables = initialize_platform_database(args.database)
    print(
        "platform_schema=READY "
        f"core_table_count={len(tables)} "
        "users_created=0 workspaces_created=0 projects_created=0 "
        "applications_created=0 scientific_state_modified=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
