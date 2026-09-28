#!/usr/bin/env python3
"""Migrate the legacy bootstrap PLATFORM_ADMIN email without changing identity.

This operator-only migration preserves the existing user id, password hash,
status, global roles, sessions, workspace/project memberships, and scientific
state. It is intentionally narrow and fail-closed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3

from nutev.tenancy import GlobalRole


def _default_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path("project_output_reference") / "platform" / "auth.sqlite3"


def _normalize_email(value: str) -> str:
    email = str(value or "").strip().casefold()
    if not email or "@" not in email or len(email) > 320:
        raise ValueError("invalid email")
    return email


def _emit(status: str, *, changed: bool) -> None:
    print(
        json.dumps(
            {
                "status": status,
                "changed": changed,
                "user_id_preserved": True,
                "credentials_modified": False,
                "workspace_or_project_access_modified": False,
                "scientific_state_modified": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _roles(payload: object) -> set[GlobalRole]:
    raw = json.loads(str(payload or "[]"))
    if not isinstance(raw, list):
        raise ValueError("global roles must be a list")
    return {GlobalRole(str(value)) for value in raw}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-email", required=True)
    parser.add_argument("--to-email", required=True)
    parser.add_argument("--database", type=Path, default=_default_database())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        source_email = _normalize_email(args.from_email)
        target_email = _normalize_email(args.to_email)
    except ValueError:
        _emit("invalid_email", changed=False)
        return 2

    if source_email == target_email:
        _emit("same_email", changed=False)
        return 0

    database = Path(args.database).expanduser().resolve()
    if not database.is_file():
        _emit("database_missing", changed=False)
        return 3

    with sqlite3.connect(database, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")

        target = connection.execute(
            """
            SELECT id, status, global_roles_json
            FROM platform_auth_users
            WHERE email = ? COLLATE NOCASE
            """,
            (target_email,),
        ).fetchone()
        source = connection.execute(
            """
            SELECT id, email, display_name, password_hash, status,
                   global_roles_json, created_at, last_login_at
            FROM platform_auth_users
            WHERE email = ? COLLATE NOCASE
            """,
            (source_email,),
        ).fetchone()

        if target is not None:
            if source is not None and str(target["id"]) != str(source["id"]):
                connection.rollback()
                _emit("target_email_conflict", changed=False)
                return 4
            try:
                target_roles = _roles(target["global_roles_json"])
            except (json.JSONDecodeError, ValueError, TypeError):
                connection.rollback()
                _emit("invalid_role_state", changed=False)
                return 5
            if str(target["status"]) != "active" or GlobalRole.PLATFORM_ADMIN not in target_roles:
                connection.rollback()
                _emit("target_not_active_platform_admin", changed=False)
                return 6
            connection.rollback()
            _emit("already_migrated", changed=False)
            return 0

        if source is None:
            connection.rollback()
            _emit("legacy_source_absent", changed=False)
            return 0

        if str(source["status"]) != "active":
            connection.rollback()
            _emit("legacy_source_not_active", changed=False)
            return 7

        try:
            source_roles = _roles(source["global_roles_json"])
        except (json.JSONDecodeError, ValueError, TypeError):
            connection.rollback()
            _emit("invalid_role_state", changed=False)
            return 5
        if GlobalRole.PLATFORM_ADMIN not in source_roles:
            connection.rollback()
            _emit("legacy_source_not_platform_admin", changed=False)
            return 8

        active_admin_ids: list[str] = []
        for row in connection.execute(
            "SELECT id, status, global_roles_json FROM platform_auth_users"
        ).fetchall():
            if str(row["status"]) != "active":
                continue
            try:
                roles = _roles(row["global_roles_json"])
            except (json.JSONDecodeError, ValueError, TypeError):
                connection.rollback()
                _emit("invalid_role_state", changed=False)
                return 5
            if GlobalRole.PLATFORM_ADMIN in roles:
                active_admin_ids.append(str(row["id"]))

        source_id = str(source["id"])
        if active_admin_ids != [source_id]:
            connection.rollback()
            _emit("ambiguous_platform_admin_state", changed=False)
            return 9

        preserved = (
            str(source["display_name"]),
            str(source["password_hash"]),
            str(source["status"]),
            str(source["global_roles_json"]),
            str(source["created_at"]),
            None if source["last_login_at"] is None else str(source["last_login_at"]),
        )

        cursor = connection.execute(
            """
            UPDATE platform_auth_users
            SET email = ?
            WHERE id = ? AND email = ? COLLATE NOCASE AND status = 'active'
            """,
            (target_email, source_id, source_email),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            _emit("concurrent_identity_change", changed=False)
            return 10

        verification = connection.execute(
            """
            SELECT id, email, display_name, password_hash, status,
                   global_roles_json, created_at, last_login_at
            FROM platform_auth_users
            WHERE id = ?
            """,
            (source_id,),
        ).fetchone()
        if verification is None:
            connection.rollback()
            _emit("verification_failed", changed=False)
            return 11

        verified_preserved = (
            str(verification["display_name"]),
            str(verification["password_hash"]),
            str(verification["status"]),
            str(verification["global_roles_json"]),
            str(verification["created_at"]),
            None if verification["last_login_at"] is None else str(verification["last_login_at"]),
        )
        if (
            str(verification["email"]).casefold() != target_email
            or verified_preserved != preserved
            or connection.execute(
                "SELECT 1 FROM platform_auth_users WHERE email = ? COLLATE NOCASE",
                (source_email,),
            ).fetchone()
            is not None
        ):
            connection.rollback()
            _emit("verification_failed", changed=False)
            return 11

        connection.commit()

    _emit("platform_admin_email_migrated", changed=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
