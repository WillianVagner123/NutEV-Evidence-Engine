#!/usr/bin/env python3
"""Issue a canonical one-time access invitation for the first platform admin.

The raw invitation token is generated at runtime by the canonical access-request
store. It is emitted only on stdout so an operator can pipe it directly into an
encryption process; it is never accepted as a CLI argument and persistence stores
only its SHA-256 digest. This command grants no global role itself.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys

from nutev.tenancy.access_requests import (
    ACCESS_REQUEST_TOKEN_TTL_SECONDS,
    SQLiteAccessRequestStore,
)

_BOOTSTRAP_ACTOR = "operator-bootstrap-first-platform-admin"


def _default_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path("project_output_reference") / "platform" / "auth.sqlite3"


def _status(status: str, *, changed: bool, request_id: str | None = None) -> None:
    payload: dict[str, object] = {
        "status": status,
        "changed": changed,
        "raw_token_persisted": False,
        "password_created": False,
        "platform_admin_granted": False,
        "workspace_or_project_access_granted": False,
        "scientific_state_modified": False,
    }
    if request_id:
        payload["request_id"] = request_id
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=sys.stderr)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--institution", required=True)
    parser.add_argument("--intended-use", required=True)
    parser.add_argument("--database", type=Path, default=_default_database())
    parser.add_argument(
        "--ttl-seconds",
        type=int,
        default=ACCESS_REQUEST_TOKEN_TTL_SECONDS,
    )
    return parser


def _active_platform_admin_count(connection: sqlite3.Connection) -> int:
    rows = connection.execute(
        "SELECT status, global_roles_json FROM platform_auth_users"
    ).fetchall()
    count = 0
    for status, payload in rows:
        try:
            roles = json.loads(str(payload or "[]"))
        except json.JSONDecodeError:
            continue
        if status == "active" and isinstance(roles, list) and "PLATFORM_ADMIN" in roles:
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    email = str(args.email or "").strip().casefold()
    display_name = " ".join(str(args.display_name or "").strip().split())
    institution = " ".join(str(args.institution or "").strip().split())
    intended_use = " ".join(str(args.intended_use or "").strip().split())
    ttl_seconds = int(args.ttl_seconds)

    if not email or "@" not in email or len(email) > 320:
        _status("invalid_email", changed=False)
        return 2
    if len(display_name) < 2 or len(display_name) > 120:
        _status("invalid_display_name", changed=False)
        return 2
    if len(institution) < 2 or len(institution) > 160:
        _status("invalid_institution", changed=False)
        return 2
    if len(intended_use) < 10 or len(intended_use) > 1200:
        _status("invalid_intended_use", changed=False)
        return 2
    if ttl_seconds < 15 * 60 or ttl_seconds > 30 * 24 * 60 * 60:
        _status("invalid_ttl", changed=False)
        return 2

    database = Path(args.database).expanduser().resolve()
    if not database.is_file():
        _status("database_missing", changed=False)
        return 3

    store = SQLiteAccessRequestStore(database)
    store.list(status="all", limit=1)

    with sqlite3.connect(database, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        if _active_platform_admin_count(connection) > 0:
            _status("already_platform_admin", changed=False)
            return 10

        user = connection.execute(
            "SELECT status FROM platform_auth_users WHERE email = ? COLLATE NOCASE LIMIT 1",
            (email,),
        ).fetchone()
        if user is not None:
            _status("existing_user_requires_role_grant", changed=False)
            return 4

        row = connection.execute(
            """
            SELECT id FROM platform_access_requests
            WHERE email = ? COLLATE NOCASE AND status IN ('pending','approved')
            ORDER BY created_at DESC LIMIT 1
            """,
            (email,),
        ).fetchone()

    if row is None:
        submitted = store.submit(
            email=email,
            display_name=display_name,
            institution=institution,
            intended_use=intended_use,
        )
        if submitted is None:
            _status("request_seed_race", changed=False)
            return 5
        request_id = submitted.id
    else:
        request_id = str(row["id"])

    try:
        invitation = store.approve(
            request_id,
            decided_by=_BOOTSTRAP_ACTOR,
            ttl_seconds=ttl_seconds,
        )
    except (KeyError, ValueError):
        _status("request_not_approvable", changed=False, request_id=request_id)
        return 6

    # IMPORTANT: stdout contains the one-time raw token and nothing else. The
    # production workflow pipes stdout directly into public-key encryption.
    print(invitation.token)
    _status("bootstrap_invitation_seeded", changed=True, request_id=request_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
