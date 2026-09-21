#!/usr/bin/env python3
"""Seed a provisional homologation (staging) platform database for access validation.

This materializes a disposable environment where the academic-supervisor access path
can be exercised end to end — a workspace owner, a workspace, a project, and an
``ACADEMIC_SUPERVISOR`` membership — without touching production identity state.

Fail-closed by construction:

* there is no default database; ``--database`` is always explicit;
* ``NUTEV_ENVIRONMENT`` must be set to a non-production value, and the variable being
  unset counts as production because the runtime itself defaults to production;
* the canonical production database path is refused outright;
* a database that already holds identities is refused rather than mutated.

Generated passwords are printed once on stdout and never persisted in raw form. They
are homologation credentials for a throwaway database and must never be reused for a
production account.

The seeded tree is navigation/tenancy state only. It creates no scientific records,
no searches, no Evidence Library content, no human review, and no PRISMA, PRESS or
GF-10 state, and it is not evidence of anything about production.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys

from nutev.tenancy import (
    SQLiteAuthProvider,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    WorkspaceRole,
    initialize_platform_database,
    new_opaque_id,
)
from nutev.tenancy.models import Principal

_PRODUCTION_RELATIVE = Path("project_output_reference") / "platform" / "auth.sqlite3"
_PRODUCTION_ENVIRONMENTS = frozenset({"", "production", "prod"})
_PASSWORD_WORDS = 4


def _emit(status: str, *, seeded: bool, **extra: object) -> None:
    payload: dict[str, object] = {
        "status": status,
        "seeded": seeded,
        "environment": "homologation",
        "production_database_touched": False,
        "scientific_state_modified": False,
        "scientific_approval_created": False,
        "prisma_press_or_gf10_state_created": False,
        "credentials_are_disposable": True,
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        required=True,
        help="Explicit path for the disposable homologation database. There is no default.",
    )
    parser.add_argument("--owner-email", default="responsavel@homologacao.invalid")
    parser.add_argument("--owner-display-name", default="Responsavel Homologacao")
    parser.add_argument("--supervisor-email", default="orientador@homologacao.invalid")
    parser.add_argument("--supervisor-display-name", default="Professor Orientador (homologacao)")
    parser.add_argument("--workspace-name", default="NutEV Homologacao")
    parser.add_argument("--workspace-slug", default="nutev-homologacao")
    parser.add_argument("--project-name", default="Projeto de Homologacao")
    parser.add_argument("--project-slug", default="projeto-homologacao")
    return parser


def _generate_password() -> str:
    return "-".join(secrets.token_hex(4) for _ in range(_PASSWORD_WORDS))


def _environment_is_production() -> bool:
    configured = str(os.environ.get("NUTEV_ENVIRONMENT") or "").strip().casefold()
    return configured in _PRODUCTION_ENVIRONMENTS


def _is_production_path(database: Path) -> bool:
    try:
        resolved = database.resolve()
    except OSError:
        return False
    if resolved.parts[-3:] == _PRODUCTION_RELATIVE.parts:
        return True
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured and Path(configured).expanduser().resolve(strict=False) == resolved:
        return True
    return False


def _existing_identity_count(database: Path) -> int:
    if not database.exists():
        return 0
    with sqlite3.connect(database, timeout=30) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='platform_auth_users'"
        ).fetchone()
        if table is None:
            return 0
        row = connection.execute("SELECT COUNT(*) FROM platform_auth_users").fetchone()
    return int(row[0]) if row else 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if _environment_is_production():
        _emit(
            "refused_production_environment",
            seeded=False,
            hint=(
                "Set NUTEV_ENVIRONMENT to a non-production value (for example "
                "'homologacao') before seeding. An unset variable counts as production."
            ),
        )
        return 2

    database = Path(args.database).expanduser()
    if _is_production_path(database):
        _emit(
            "refused_production_database_path",
            seeded=False,
            hint="Point --database at a disposable homologation file, never the production store.",
        )
        return 3

    if database.exists() and database.is_symlink():
        _emit("refused_symlink_database", seeded=False)
        return 4

    existing = _existing_identity_count(database)
    if existing > 0:
        _emit(
            "refused_populated_database",
            seeded=False,
            existing_identity_count=existing,
            hint="Delete the homologation file or choose a new path; this tool never mutates identities.",
        )
        return 5

    initialize_platform_database(database)
    auth = SQLiteAuthProvider(database)
    store = SQLiteWorkspaceProjectStore(database)
    access = WorkspaceProjectService(store)

    owner_password = _generate_password()
    supervisor_password = _generate_password()

    try:
        owner = auth.provision_user(
            email=str(args.owner_email),
            display_name=str(args.owner_display_name),
            password=owner_password,
        )
        supervisor = auth.provision_user(
            email=str(args.supervisor_email),
            display_name=str(args.supervisor_display_name),
            password=supervisor_password,
        )
    except ValueError as exc:
        _emit("identity_refused", seeded=False, reason=str(exc))
        return 6

    workspace = access.provision_workspace(
        owner_user_id=owner.id,
        name=str(args.workspace_name),
        slug=str(args.workspace_slug),
    )
    owner_principal = Principal(
        user_id=owner.id,
        workspace_memberships=tuple(store.memberships_for_user(owner.id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )
    project = access.create_project(
        owner_principal,
        workspace_id=workspace.id,
        name=str(args.project_name),
        slug=str(args.project_slug),
    )
    membership = store.upsert_membership(
        workspace_id=workspace.id,
        user_id=supervisor.id,
        role=WorkspaceRole.ACADEMIC_SUPERVISOR,
    )

    print(
        "HOMOLOGATION ONLY — disposable credentials, never production identities.",
        file=sys.stderr,
    )
    _emit(
        "homologation_seeded",
        seeded=True,
        database=str(database.resolve()),
        workspace={"id": workspace.id, "slug": workspace.slug, "name": workspace.name},
        project={"id": project.id, "slug": project.slug, "name": project.name},
        owner={"user_id": owner.id, "email": owner.email, "password": owner_password},
        supervisor={
            "user_id": supervisor.id,
            "email": supervisor.email,
            "password": supervisor_password,
            "role": membership.role.value,
        },
        serve_with=(
            "NUTEV_AUTH_MODE=pilot NUTEV_ENVIRONMENT=homologacao "
            f"NUTEV_AUTH_DB={database.resolve()} "
            "python apps/nutev-web/secure_server.py --host 127.0.0.1 --port 8765"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
