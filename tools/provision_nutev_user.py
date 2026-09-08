#!/usr/bin/env python3
from __future__ import annotations

import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import sys

from nutev.tenancy import GlobalRole, SQLiteAuthProvider


def _default_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path("project_output_reference") / "platform" / "auth.sqlite3"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Provision a NutEV platform identity using Argon2. Password input is read "
            "interactively and is never accepted as a command-line argument."
        )
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--database", type=Path, default=_default_database())
    parser.add_argument(
        "--platform-admin",
        action="store_true",
        help=(
            "Grant the global PLATFORM_ADMIN infrastructure role. This does not grant "
            "implicit access to private scientific workspace/project data."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    password = getpass("New NutEV password: ")
    confirmation = getpass("Confirm NutEV password: ")
    if password != confirmation:
        print("Password confirmation does not match.", file=sys.stderr)
        return 2

    roles = {GlobalRole.PLATFORM_ADMIN} if args.platform_admin else set()
    provider = SQLiteAuthProvider(args.database)
    try:
        user = provider.provision_user(
            email=args.email,
            display_name=args.display_name,
            password=password,
            global_roles=roles,
        )
    except ValueError as exc:
        print(f"Provisioning refused: {exc}", file=sys.stderr)
        return 3

    print(
        json.dumps(
            {
                "status": "provisioned",
                "user_id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "global_roles": sorted(role.value for role in roles),
                "database": str(Path(args.database)),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
