#!/usr/bin/env python3
"""Seed a one-time access invitation for the first platform administrator.

The raw invitation token is deliberately NOT accepted by this command. Operators
provide only its SHA-256 digest, so the raw token never enters Git, Actions logs,
or persistent storage. The invited identity still creates its own password through
the canonical access-invitation flow. This command grants no global role itself.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sqlite3

from nutev.tenancy.access_requests import SQLiteAccessRequestStore

_TOKEN_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_BOOTSTRAP_ACTOR = "operator-bootstrap-first-platform-admin"
_DEFAULT_TTL_SECONDS = 72 * 60 * 60


def _default_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path("project_output_reference") / "platform" / "auth.sqlite3"


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _emit(status: str, *, changed: bool, request_id: str | None = None) -> None:
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
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--institution", required=True)
    parser.add_argument("--intended-use", required=True)
    parser.add_argument("--token-digest", required=True)
    parser.add_argument("--database", type=Path, default=_default_database())
    parser.add_argument("--ttl-seconds", type=int, default=_DEFAULT_TTL_SECONDS)
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
    digest = str(args.token_digest or "").strip().casefold()
    ttl_seconds = int(args.ttl_seconds)

    if not email or "@" not in email or len(email) > 320:
        _emit("invalid_email", changed=False)
        return 2
    if len(display_name) < 2 or len(display_name) > 120:
        _emit("invalid_display_name", changed=False)
        return 2
    if len(institution) < 2 or len(institution) > 160:
        _emit("invalid_institution", changed=False)
        return 2
    if len(intended_use) < 10 or len(intended_use) > 1200:
        _emit("invalid_intended_use", changed=False)
        return 2
    if not _TOKEN_DIGEST_RE.fullmatch(digest):
        _emit("invalid_token_digest", changed=False)
        return 2
    if ttl_seconds < 15 * 60 or ttl_seconds > 30 * 24 * 60 * 60:
        _emit("invalid_ttl", changed=False)
        return 2

    database = Path(args.database).expanduser().resolve()
    if not database.is_file():
        _emit("database_missing", changed=False)
        return 3

    # Ensure the access-request schema exists using the canonical store.
    store = SQLiteAccessRequestStore(database)
    store.list(status="all", limit=1)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)

    with sqlite3.connect(database, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        if _active_platform_admin_count(connection) > 0:
            _emit("already_platform_admin", changed=False)
            return 0

        user = connection.execute(
            "SELECT status FROM platform_auth_users WHERE email = ? COLLATE NOCASE LIMIT 1",
            (email,),
        ).fetchone()
        if user is not None:
            _emit("existing_user_requires_role_grant", changed=False)
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
            _emit("request_seed_race", changed=False)
            return 5
        request_id = submitted.id
    else:
        request_id = str(row["id"])

    with sqlite3.connect(database, timeout=30) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            """
            UPDATE platform_access_requests
            SET display_name=?, institution=?, intended_use=?, status='approved',
                decided_at=?, decided_by=?, rejection_reason=NULL,
                invitation_token_hash=?, invitation_expires_at=?,
                accepted_at=NULL, accepted_user_id=NULL
            WHERE id=? AND status IN ('pending','approved')
            """,
            (
                display_name,
                institution,
                intended_use,
                _iso(now),
                _BOOTSTRAP_ACTOR,
                digest,
                _iso(expires_at),
                request_id,
            ),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            _emit("request_changed_during_seed", changed=False)
            return 6
        connection.commit()

    _emit("bootstrap_invitation_seeded", changed=True, request_id=request_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
