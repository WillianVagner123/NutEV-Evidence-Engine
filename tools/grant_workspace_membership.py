#!/usr/bin/env python3
"""Grant a workspace membership role to an existing active NutEV identity.

This is an operator-only, idempotent membership mutation intended for governed
onboarding steps such as attaching an academic supervisor ("professor
orientador") to a workspace with the read-only ``ACADEMIC_SUPERVISOR`` role.

It never creates users, sets or resets passwords, creates workspaces or
projects, grants global roles, or mutates scientific state. It cannot assign
``WORKSPACE_OWNER``; ownership changes must use the explicit transfer flow.

Membership is an access grant only. It is not scientific approval and does not
create eligibility, methodological quality, risk of bias, certainty,
recommendation, PRISMA state, PRESS, GF-10 or query-freeze authorization.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3

from nutev.tenancy import (
    MembershipStatus,
    SQLiteWorkspaceProjectStore,
    WorkspaceRole,
)

_ASSIGNABLE_ROLES = tuple(
    role.value for role in WorkspaceRole if role is not WorkspaceRole.WORKSPACE_OWNER
)
_ASSIGNABLE_STATUSES = (
    MembershipStatus.INVITED.value,
    MembershipStatus.ACTIVE.value,
    MembershipStatus.SUSPENDED.value,
)


def _default_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path("project_output_reference") / "platform" / "auth.sqlite3"


def _emit(status: str, *, changed: bool, **extra: object) -> None:
    payload: dict[str, object] = {
        "status": status,
        "changed": changed,
        "user_created": False,
        "password_created": False,
        "global_role_granted": False,
        "workspace_created": False,
        "project_created": False,
        "scientific_state_modified": False,
        "scientific_approval_created": False,
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--workspace-id")
    target.add_argument("--workspace-slug")
    parser.add_argument("--role", required=True, choices=_ASSIGNABLE_ROLES)
    parser.add_argument(
        "--status",
        default=MembershipStatus.ACTIVE.value,
        choices=_ASSIGNABLE_STATUSES,
    )
    parser.add_argument("--database", type=Path, default=_default_database())
    parser.add_argument(
        "--allow-role-change",
        action="store_true",
        help=(
            "Permit replacing an existing membership that currently holds a different "
            "role. Without this flag an existing differing role is refused fail-closed."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    email = str(args.email or "").strip().casefold()
    if not email or "@" not in email or len(email) > 320:
        _emit("invalid_email", changed=False)
        return 2

    role = WorkspaceRole(str(args.role))
    if role is WorkspaceRole.WORKSPACE_OWNER:
        _emit("owner_role_refused", changed=False)
        return 7
    status = MembershipStatus(str(args.status))

    database = Path(args.database).expanduser().resolve()
    if not database.is_file():
        _emit("database_missing", changed=False)
        return 3

    with sqlite3.connect(database, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        user = connection.execute(
            "SELECT id, status FROM platform_auth_users WHERE email = ? COLLATE NOCASE",
            (email,),
        ).fetchone()
        if user is None:
            _emit("user_not_found", changed=False)
            return 4
        if str(user["status"]) != "active":
            _emit("user_not_active", changed=False, user_status=str(user["status"]))
            return 5
        user_id = str(user["id"])

        if args.workspace_id:
            workspace = connection.execute(
                "SELECT id, slug, status FROM platform_workspaces WHERE id = ?",
                (str(args.workspace_id),),
            ).fetchone()
        else:
            workspace = connection.execute(
                "SELECT id, slug, status FROM platform_workspaces WHERE slug = ?",
                (str(args.workspace_slug),),
            ).fetchone()
        if workspace is None:
            _emit("workspace_not_found", changed=False)
            return 6
        if str(workspace["status"]) != "active":
            _emit(
                "workspace_not_active",
                changed=False,
                workspace_status=str(workspace["status"]),
            )
            return 10
        workspace_id = str(workspace["id"])

        existing = connection.execute(
            """
            SELECT role, status FROM platform_workspace_memberships
            WHERE workspace_id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

    if existing is not None:
        current_role = str(existing["role"])
        current_status = str(existing["status"])
        if current_role == role.value and current_status == status.value:
            _emit(
                "already_granted",
                changed=False,
                user_id=user_id,
                workspace_id=workspace_id,
                role=role.value,
                membership_status=status.value,
            )
            return 0
        if current_role == WorkspaceRole.WORKSPACE_OWNER.value:
            _emit("owner_membership_refused", changed=False, workspace_id=workspace_id)
            return 7
        if current_role != role.value and not args.allow_role_change:
            _emit(
                "role_change_requires_explicit_flag",
                changed=False,
                user_id=user_id,
                workspace_id=workspace_id,
                current_role=current_role,
                requested_role=role.value,
            )
            return 8

    store = SQLiteWorkspaceProjectStore(database)
    try:
        # invited_by stays NULL: an operator CLI grant has no authenticated
        # inviting Principal and must not impersonate one.
        membership = store.upsert_membership(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            status=status,
        )
    except (KeyError, ValueError) as exc:
        _emit("membership_refused", changed=False, reason=str(exc))
        return 9

    if (
        membership.workspace_id != workspace_id
        or membership.user_id != user_id
        or membership.role is not role
        or membership.status is not status
    ):
        _emit("verification_failed", changed=False)
        return 9

    _emit(
        "membership_granted",
        changed=True,
        user_id=user_id,
        workspace_id=workspace_id,
        role=role.value,
        membership_status=status.value,
        previous_role=str(existing["role"]) if existing is not None else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
