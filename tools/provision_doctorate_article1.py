#!/usr/bin/env python3
"""Materialize the doctorate workspace, the Article 1 project and its ResearchApplication.

Operator-only and idempotent. It creates tenancy and project-configuration state for an
identity that already exists, so an operator does not have to hand-write Python against the
production database to open the workspace for the first time.

It never creates users, sets or resets passwords, grants global roles, or touches scientific
state. Re-running it reuses whatever is already there and never overwrites a project's private
application configuration.

Configuring a ResearchApplication is not methodological approval. This command does not
execute a search, include or exclude a record, approve PRESS, authorize GF-10, freeze queries,
activate historical ownership or create PRISMA events. Binding the project to the historical
Article 1 material stays a separate, explicitly evidenced human step: the server-managed
``NUTEV_A1_WORKSPACE_ID`` / ``NUTEV_A1_PROJECT_ID`` pins, which this command only reports.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3

from nutev.applications.willian_doctorate_a1 import load_d132_config
from nutev.tenancy import (
    ApplicationService,
    Principal,
    SCOPING_REVIEW,
    SQLiteApplicationStore,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    new_opaque_id,
)

# The assembly id the first-party Article 1 adapters look for. On its own it is not ownership:
# access to the historical material is gated by the server-managed owner pins.
A1_ASSEMBLY_ID = "WILLIAN_DOCTORATE_A1"
_REPO_ROOT = Path(__file__).resolve().parents[1]


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
        "membership_granted_to_others": False,
        "historical_binding_activated": False,
        "scientific_state_modified": False,
        "scientific_approval_created": False,
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-email", required=True, help="existing active account that will own the workspace")
    parser.add_argument("--workspace-name", required=True)
    parser.add_argument("--workspace-slug", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--project-slug", required=True)
    parser.add_argument("--project-description", default="")
    parser.add_argument("--project-type", default="review")
    parser.add_argument(
        "--article1-assembly",
        action="store_true",
        help=(
            "tag the application configuration with the Article 1 assembly id. This is "
            "configuration, not ownership: the server-managed owner pins remain required "
            "and remain a separate human step."
        ),
    )
    parser.add_argument("--database", type=Path, default=_default_database())
    return parser


def _lookup_owner(database: Path, email: str) -> tuple[str, str] | None:
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT id, status FROM platform_auth_users WHERE email = ? COLLATE NOCASE",
            (email,),
        ).fetchone()
    return (str(row["id"]), str(row["status"])) if row is not None else None


def _workspace_by_slug(store: SQLiteWorkspaceProjectStore, slug: str):
    with sqlite3.connect(f"file:{store.database_path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT id FROM platform_workspaces WHERE slug = ? AND status = 'active'",
            (slug,),
        ).fetchone()
    return store.get_workspace(str(row["id"])) if row is not None else None


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    email = str(args.owner_email or "").strip().casefold()
    if not email or "@" not in email or len(email) > 320:
        _emit("invalid_email", changed=False)
        return 2

    database = Path(args.database).expanduser()
    if database.is_symlink() or not database.is_file():
        _emit("database_missing", changed=False)
        return 3

    owner = _lookup_owner(database, email)
    if owner is None:
        # Identities come from the governed invitation flow, never from this command.
        _emit("owner_not_found", changed=False)
        return 4
    owner_id, owner_status = owner
    if owner_status != "active":
        _emit("owner_not_active", changed=False, owner_status=owner_status)
        return 5

    store = SQLiteWorkspaceProjectStore(database)
    access = WorkspaceProjectService(store)
    applications = ApplicationService(SQLiteApplicationStore(database), access)

    workspace_created = False
    workspace = _workspace_by_slug(store, str(args.workspace_slug).strip().casefold())
    if workspace is None:
        try:
            workspace = access.provision_workspace(
                owner_user_id=owner_id,
                name=str(args.workspace_name),
                slug=str(args.workspace_slug),
            )
            workspace_created = True
        except ValueError as exc:
            _emit("workspace_refused", changed=False, reason=str(exc))
            return 6
    elif workspace.owner_user_id != owner_id:
        # Never silently retarget an existing workspace at a different owner.
        _emit("workspace_owned_by_another_identity", changed=False, workspace_id=workspace.id)
        return 7

    principal = Principal(
        user_id=owner_id,
        workspace_memberships=tuple(access.memberships_for_user(owner_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )

    project_created = False
    project_slug = str(args.project_slug).strip().casefold()
    project = next(
        (item for item in store.list_projects(workspace.id) if item.slug == project_slug),
        None,
    )
    if project is None:
        try:
            project = access.create_project(
                principal,
                workspace_id=workspace.id,
                name=str(args.project_name),
                slug=str(args.project_slug),
                description=str(args.project_description or ""),
                project_type=str(args.project_type or "review"),
            )
            project_created = True
        except (PermissionError, ValueError, KeyError) as exc:
            _emit(
                "project_refused",
                changed=workspace_created,
                workspace_id=workspace.id,
                reason=type(exc).__name__,
            )
            return 8

    application_created = False
    application_updated = False
    try:
        application = applications.get(principal, workspace_id=workspace.id, project_id=project.id)
    except (PermissionError, ValueError, KeyError):
        application = None

    d132_version = load_d132_config(_REPO_ROOT).config_version if args.article1_assembly else None
    required_article1_configuration = (
        {
            "assembly_id": A1_ASSEMBLY_ID,
            "d132_config_version": d132_version,
        }
        if args.article1_assembly
        else {}
    )

    if application is None:
        try:
            application = applications.configure(
                principal,
                workspace_id=workspace.id,
                project_id=project.id,
                template_id=SCOPING_REVIEW,
                configuration=required_article1_configuration,
            )
            application_created = True
        except (PermissionError, ValueError, KeyError) as exc:
            _emit(
                "application_refused",
                changed=workspace_created or project_created,
                workspace_id=workspace.id,
                project_id=project.id,
                reason=type(exc).__name__,
            )
            return 9
    elif args.article1_assembly:
        descriptor = application.descriptor()
        configuration = descriptor.get("configuration")
        if not isinstance(configuration, dict):
            _emit(
                "application_binding_conflict",
                changed=workspace_created or project_created,
                workspace_id=workspace.id,
                project_id=project.id,
                reason="configuration_not_object",
            )
            return 10

        conflicts = {
            key: configuration.get(key)
            for key, expected in required_article1_configuration.items()
            if key in configuration and configuration.get(key) != expected
        }
        if conflicts:
            _emit(
                "application_binding_conflict",
                changed=workspace_created or project_created,
                workspace_id=workspace.id,
                project_id=project.id,
                conflicting_keys=sorted(conflicts),
            )
            return 10

        missing = {
            key: value
            for key, value in required_article1_configuration.items()
            if configuration.get(key) != value
        }
        if missing:
            merged_configuration = dict(configuration)
            merged_configuration.update(missing)
            try:
                application = applications.configure(
                    principal,
                    workspace_id=workspace.id,
                    project_id=project.id,
                    application_type=str(descriptor.get("application_type") or ""),
                    template_id=str(descriptor.get("template_id") or "") or None,
                    template_version=str(descriptor.get("template_version") or "") or None,
                    config_version=str(descriptor.get("config_version") or "1"),
                    configuration=merged_configuration,
                )
                application_updated = True
            except (PermissionError, ValueError, KeyError) as exc:
                _emit(
                    "application_refused",
                    changed=workspace_created or project_created,
                    workspace_id=workspace.id,
                    project_id=project.id,
                    reason=type(exc).__name__,
                )
                return 9

    descriptor = application.descriptor()
    changed = workspace_created or project_created or application_created or application_updated
    _emit(
        "provisioned" if changed else "already_provisioned",
        changed=changed,
        workspace_id=workspace.id,
        workspace_slug=workspace.slug,
        workspace_created=workspace_created,
        project_id=project.id,
        project_slug=project.slug,
        project_created=project_created,
        application_id=descriptor.get("id"),
        application_type=descriptor.get("application_type"),
        template_id=descriptor.get("template_id"),
        application_created=application_created,
        application_updated=application_updated,
        article1_assembly_configured=descriptor.get("configuration", {}).get("assembly_id") == A1_ASSEMBLY_ID,
        d132_config_version=descriptor.get("configuration", {}).get("d132_config_version"),
        # The remaining human steps, stated rather than performed.
        next_steps=[
            "set NUTEV_A1_WORKSPACE_ID and NUTEV_A1_PROJECT_ID to these ids, from reviewed "
            "runtime ownership evidence, to expose the Article 1 surfaces",
            "grant ACADEMIC_SUPERVISOR to the supervisor after they complete the governed "
            "invitation and set their own password",
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
