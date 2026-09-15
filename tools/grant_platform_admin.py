#!/usr/bin/env python3
"""Grant PLATFORM_ADMIN to an existing active NutEV identity.

This is an operator-only, idempotent role mutation. It never creates users,
changes passwords, grants workspace/project membership, or mutates scientific
state.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys

from nutev.tenancy import GlobalRole


def _default_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path("project_output_reference") / "platform" / "auth.sqlite3"


def _emit(status: str, *, changed: bool, roles: set[GlobalRole] | None = None) -> None:
    payload: dict[str, object] = {
        "status": status,
        "changed": changed,
        "scientific_state_modified": False,
        "workspace_or_project_access_granted": False,
    }
    if roles is not None:
        payload["global_roles"] = sorted(role.value for role in roles)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--database", type=Path, default=_default_database())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    email = str(args.email or "").strip().casefold()
    if not email or "@" not in email or len(email) > 320:
        _emit("invalid_email", changed=False)
        return 2

    database = Path(args.database).expanduser().resolve()
    if not database.is_file():
        _emit("database_missing", changed=False)
        return 3

    with sqlite3.connect(database, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        row = connection.execute(
            """
            SELECT id, status, global_roles_json
            FROM platform_auth_users
            WHERE email = ? COLLATE NOCASE
            """,
            (email,),
        ).fetchone()
        if row is None:
            _emit("user_not_found", changed=False)
            return 4
        if str(row["status"]) != "active":
            _emit("user_not_active", changed=False)
            return 5

        try:
            raw_roles = json.loads(str(row["global_roles_json"] or "[]"))
            if not isinstance(raw_roles, list):
                raise ValueError("global roles must be a list")
            roles = {GlobalRole(str(value)) for value in raw_roles}
        except (json.JSONDecodeError, ValueError, TypeError):
            _emit("invalid_role_state", changed=False)
            return 6

        target = GlobalRole.PLATFORM_ADMIN
        if target in roles:
            _emit("already_platform_admin", changed=False, roles=roles)
            return 0

        updated_roles = set(roles)
        updated_roles.add(target)
        encoded = json.dumps(
            sorted(role.value for role in updated_roles),
            ensure_ascii=False,
            separators=(",", ":"),
        )

        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            """
            UPDATE platform_auth_users
            SET global_roles_json = ?
            WHERE id = ? AND status = 'active'
            """,
            (encoded, str(row["id"])),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            _emit("concurrent_user_state_change", changed=False)
            return 7
        connection.commit()

        verification = connection.execute(
            "SELECT global_roles_json FROM platform_auth_users WHERE id = ?",
            (str(row["id"]),),
        ).fetchone()
        if verification is None:
            _emit("verification_failed", changed=False)
            return 8
        verified_raw = json.loads(str(verification["global_roles_json"] or "[]"))
        verified_roles = {GlobalRole(str(value)) for value in verified_raw}
        if target not in verified_roles:
            _emit("verification_failed", changed=False, roles=verified_roles)
            return 8

    _emit("platform_admin_granted", changed=True, roles=verified_roles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
