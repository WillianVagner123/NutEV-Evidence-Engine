#!/usr/bin/env python3
"""Create a workspace, and optionally a project inside it, for an existing identity.

This is an operator-only, idempotent, fail-closed provisioning step for a hosted
deployment that has no workspace yet. Without a workspace no membership can be
granted, so a supervisor cannot be attached to anything.

It never creates an account, sets a password, issues an invitation or grants a
global role. The owner must already exist and be active; the workspace is created
under that identity, and the canonical store gives them the WORKSPACE_OWNER
membership as part of creating it.

What it creates is tenancy and navigation state. It configures no research
application and creates no scientific record, search, Evidence Library content,
human review, PRISMA, PRESS or GF-10 state. A workspace existing says nothing
about eligibility, quality, certainty, recommendation or scientific approval.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3

from nutev.tenancy import SQLiteWorkspaceProjectStore


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
        "invitation_issued": False,
        "global_role_granted": False,
        "research_application_configured": False,
        "scientific_state_modified": False,
        "scientific_approval_created": False,
        "prisma_press_or_gf10_state_created": False,
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owner-email",
        required=True,
        help="Existing active account that will own the workspace.",
    )
    parser.add_argument("--workspace-name", required=True)
    parser.add_argument("--workspace-slug", required=True)
    parser.add_argument(
        "--project-name",
        help="Create a project too. Requires --project-slug.",
    )
    parser.add_argument("--project-slug")
    parser.add_argument("--project-type", default="generic")
    parser.add_argument("--project-description", default="")
    parser.add_argument("--database", type=Path, default=_default_database())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    email = str(args.owner_email or "").strip().casefold()
    if not email or "@" not in email or len(email) > 320:
        _emit("invalid_owner_email", changed=False)
        return 2
    if bool(args.project_name) != bool(args.project_slug):
        _emit("project_name_and_slug_must_be_given_together", changed=False)
        return 2

    database = Path(args.database).expanduser().resolve()
    if not database.is_file():
        _emit("database_missing", changed=False, database=str(database))
        return 3

    with sqlite3.connect(database, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        owner = connection.execute(
            "SELECT id, email, display_name, status FROM platform_auth_users "
            "WHERE email = ? COLLATE NOCASE",
            (email,),
        ).fetchone()
        if owner is None:
            # The count distinguishes "this platform has no accounts at all" from
            # "the supplied address is not the one that was provisioned". Only the
            # count is reported; no other person's address is disclosed.
            total = int(
                connection.execute("SELECT COUNT(*) FROM platform_auth_users").fetchone()[0]
            )
            _emit(
                "owner_not_found",
                changed=False,
                accounts_on_platform=total,
                hint=(
                    "No account has been provisioned at all; complete the first-admin "
                    "bootstrap before creating a workspace."
                    if total == 0
                    else "Accounts exist but not under this address; check which address was used."
                ),
            )
            return 4
        if str(owner["status"]) != "active":
            _emit("owner_not_active", changed=False, owner_status=str(owner["status"]))
            return 5
        owner_id = str(owner["id"])

        existing_workspace = connection.execute(
            "SELECT id, name, slug, owner_user_id, status FROM platform_workspaces WHERE slug = ?",
            (str(args.workspace_slug or "").strip().casefold(),),
        ).fetchone()

    store = SQLiteWorkspaceProjectStore(database)
    workspace_changed = False

    if existing_workspace is None:
        try:
            workspace = store.create_workspace(
                owner_user_id=owner_id,
                name=str(args.workspace_name),
                slug=str(args.workspace_slug),
            )
        except ValueError as exc:
            _emit("workspace_refused", changed=False, reason=str(exc))
            return 6
        workspace_changed = True
        workspace_id = workspace.id
        workspace_slug = workspace.slug
        workspace_name = workspace.name
    else:
        # Reuse rather than duplicate, but never silently adopt a workspace that
        # belongs to somebody else: that would hand its projects to this owner.
        if str(existing_workspace["owner_user_id"]) != owner_id:
            _emit(
                "workspace_slug_owned_by_another_identity",
                changed=False,
                workspace_id=str(existing_workspace["id"]),
                hint="Choose a different slug, or use the explicit ownership-transfer flow.",
            )
            return 6
        if str(existing_workspace["status"]) != "active":
            _emit(
                "workspace_not_active",
                changed=False,
                workspace_status=str(existing_workspace["status"]),
            )
            return 6
        workspace_id = str(existing_workspace["id"])
        workspace_slug = str(existing_workspace["slug"])
        workspace_name = str(existing_workspace["name"])

    project_payload: dict[str, object] | None = None
    project_changed = False

    if args.project_slug:
        requested_slug = str(args.project_slug).strip().casefold()
        with sqlite3.connect(database, timeout=30) as connection:
            connection.row_factory = sqlite3.Row
            existing_project = connection.execute(
                "SELECT id, name, slug, status FROM platform_projects "
                "WHERE workspace_id = ? AND slug = ?",
                (workspace_id, requested_slug),
            ).fetchone()

        if existing_project is None:
            try:
                project = store.create_project(
                    workspace_id=workspace_id,
                    name=str(args.project_name),
                    slug=str(args.project_slug),
                    created_by=owner_id,
                    description=str(args.project_description or ""),
                    project_type=str(args.project_type or "generic"),
                )
            except (ValueError, KeyError) as exc:
                _emit(
                    "project_refused",
                    changed=workspace_changed,
                    reason=str(exc),
                    workspace_id=workspace_id,
                )
                return 7
            project_changed = True
            project_payload = {
                "id": project.id,
                "name": project.name,
                "slug": project.slug,
                "project_type": project.project_type,
            }
        else:
            project_payload = {
                "id": str(existing_project["id"]),
                "name": str(existing_project["name"]),
                "slug": str(existing_project["slug"]),
                "status": str(existing_project["status"]),
            }

    changed = workspace_changed or project_changed
    if changed:
        status = "provisioned"
    else:
        status = "already_present"

    _emit(
        status,
        changed=changed,
        owner={"user_id": owner_id, "email": str(owner["email"])},
        workspace={
            "id": workspace_id,
            "name": workspace_name,
            "slug": workspace_slug,
            "created_now": workspace_changed,
        },
        project=(
            {**project_payload, "created_now": project_changed}
            if project_payload is not None
            else None
        ),
        next_step=(
            "The owner holds WORKSPACE_OWNER. A research application is still "
            "unconfigured, and a supervisor still completes access request, "
            "approval and password before a membership can be granted."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
