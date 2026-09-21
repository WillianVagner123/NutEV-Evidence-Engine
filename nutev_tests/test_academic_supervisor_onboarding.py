"""Governed onboarding contract for the ACADEMIC_SUPERVISOR ("professor orientador") role.

Covers the full hosted path an academic supervisor actually travels — public access
request, administrative approval, invited person setting their own password, operator
membership grant, login — and asserts the resulting authorization envelope stays
read-only and workspace-scoped.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from argon2 import PasswordHasher
import pytest

from nutev.tenancy import (
    Permission,
    PermissionService,
    SQLiteAuthProvider,
    SQLiteSessionStore,
    SQLiteWorkspaceProjectStore,
    SessionPrincipalService,
    WorkspaceProjectService,
    WorkspaceRole,
    initialize_platform_database,
)
from nutev.tenancy.access_requests import SQLiteAccessRequestStore

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "grant_workspace_membership.py"
SPEC = importlib.util.spec_from_file_location("grant_workspace_membership", MODULE_PATH)
assert SPEC and SPEC.loader
grant_tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = grant_tool
SPEC.loader.exec_module(grant_tool)

OWNER_PASSWORD = "a sufficiently long owner password"
SUPERVISOR_PASSWORD = "uma senha longa do orientador"

_WRITE_PERMISSIONS = (
    Permission.SCREEN,
    Permission.EXTRACT,
    Permission.ADJUDICATE,
    Permission.EVIDENCE_LIBRARY_WRITE,
    Permission.FULL_TEXT_ACCESS_MANAGE,
    Permission.APPLICATION_MANAGE,
    Permission.HUMAN_REVIEW_MANAGE,
    Permission.SEARCH_RUN,
    Permission.MEMBERS_MANAGE,
    Permission.PROJECT_CREATE,
    Permission.PROJECT_DELETE,
    Permission.WORKSPACE_SETTINGS_MANAGE,
)


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)


def _run_tool(argv: list[str], capsys) -> tuple[int, dict]:
    code = grant_tool.main(argv)
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    return code, payload


@pytest.fixture()
def platform(tmp_path: Path):
    database = tmp_path / "auth.sqlite3"
    initialize_platform_database(database)
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    store = SQLiteWorkspaceProjectStore(database)
    access = WorkspaceProjectService(store)
    logins = SessionPrincipalService(
        auth_provider=auth,
        session_store=SQLiteSessionStore(database),
        membership_loader=store.memberships_for_user,
    )
    owner = auth.provision_user(
        email="owner@example.org",
        display_name="Owner",
        password=OWNER_PASSWORD,
    )
    workspace = access.provision_workspace(
        owner_user_id=owner.id,
        name="NutEV Doutorado",
        slug="nutev-doutorado",
    )
    owner_principal = logins.login("owner@example.org", OWNER_PASSWORD).session.principal
    project = access.create_project(
        owner_principal,
        workspace_id=workspace.id,
        name="Artigo 1",
        slug="artigo-1",
    )
    return {
        "database": database,
        "auth": auth,
        "access": access,
        "logins": logins,
        "owner": owner,
        "workspace": workspace,
        "project": project,
    }


def _onboard_supervisor(platform) -> object:
    """Walk the governed request -> approve -> accept path and return the new user."""

    requests = SQLiteAccessRequestStore(platform["database"])
    submitted = requests.submit(
        email="orientador@universidade.br",
        display_name="Prof. Orientador",
        institution="Universidade",
        intended_use="Acompanhamento academico do Artigo 1.",
    )
    assert submitted is not None
    invitation = requests.approve(submitted.id, decided_by=platform["owner"].id)
    return requests.accept_invitation(invitation.token, password=SUPERVISOR_PASSWORD)


def test_supervisor_account_has_no_access_before_membership_is_granted(platform) -> None:
    _onboard_supervisor(platform)
    result = platform["logins"].login("orientador@universidade.br", SUPERVISOR_PASSWORD)

    assert result is not None
    assert result.session.principal.workspace_memberships == ()
    with pytest.raises(PermissionError, match="workspace_access_denied"):
        platform["access"].list_projects(
            result.session.principal,
            platform["workspace"].id,
        )


def test_granted_supervisor_can_log_in_and_read_but_never_write(platform, capsys) -> None:
    _onboard_supervisor(platform)
    code, payload = _run_tool(
        [
            "--email",
            "orientador@universidade.br",
            "--workspace-slug",
            "nutev-doutorado",
            "--role",
            "ACADEMIC_SUPERVISOR",
            "--database",
            str(platform["database"]),
        ],
        capsys,
    )
    assert code == 0
    assert payload["status"] == "membership_granted"
    assert payload["changed"] is True
    assert payload["user_created"] is False
    assert payload["password_created"] is False
    assert payload["global_role_granted"] is False
    assert payload["scientific_state_modified"] is False
    assert payload["scientific_approval_created"] is False

    result = platform["logins"].login("orientador@universidade.br", SUPERVISOR_PASSWORD)
    principal = result.session.principal
    membership = principal.membership_for(platform["workspace"].id)
    assert membership is not None
    assert membership.role is WorkspaceRole.ACADEMIC_SUPERVISOR
    assert membership.invited_by is None

    access = platform["access"]
    assert [p.id for p in access.list_projects(principal, platform["workspace"].id)] == [
        platform["project"].id
    ]

    context = access.authorization_context(
        principal,
        workspace_id=platform["workspace"].id,
        project_id=platform["project"].id,
    )
    permissions = PermissionService()
    for readable in (
        Permission.APPLICATION_READ,
        Permission.SEARCH_HISTORY_READ,
        Permission.EVIDENCE_LIBRARY_READ,
        Permission.FULL_TEXT_ACCESS_READ,
        Permission.PROJECT_BANK_READ,
        Permission.HUMAN_REVIEW_READ,
        Permission.PROJECT_AUDIT_READ,
    ):
        assert permissions.can(principal, readable, context=context), readable
    for withheld in _WRITE_PERMISSIONS:
        assert not permissions.can(principal, withheld, context=context), withheld


def test_grant_is_idempotent(platform, capsys) -> None:
    _onboard_supervisor(platform)
    argv = [
        "--email",
        "orientador@universidade.br",
        "--workspace-slug",
        "nutev-doutorado",
        "--role",
        "ACADEMIC_SUPERVISOR",
        "--database",
        str(platform["database"]),
    ]
    assert _run_tool(argv, capsys)[1]["changed"] is True
    code, payload = _run_tool(argv, capsys)
    assert code == 0
    assert payload["status"] == "already_granted"
    assert payload["changed"] is False


def test_grant_refuses_silent_role_change(platform, capsys) -> None:
    _onboard_supervisor(platform)
    base = [
        "--email",
        "orientador@universidade.br",
        "--workspace-slug",
        "nutev-doutorado",
        "--database",
        str(platform["database"]),
    ]
    _run_tool([*base, "--role", "ACADEMIC_SUPERVISOR"], capsys)

    code, payload = _run_tool([*base, "--role", "RESEARCHER"], capsys)
    assert code == 8
    assert payload["status"] == "role_change_requires_explicit_flag"
    assert payload["changed"] is False
    assert payload["current_role"] == "ACADEMIC_SUPERVISOR"

    result = platform["logins"].login("orientador@universidade.br", SUPERVISOR_PASSWORD)
    membership = result.session.principal.membership_for(platform["workspace"].id)
    assert membership is not None
    assert membership.role is WorkspaceRole.ACADEMIC_SUPERVISOR

    code, payload = _run_tool([*base, "--role", "RESEARCHER", "--allow-role-change"], capsys)
    assert code == 0
    assert payload["status"] == "membership_granted"
    assert payload["previous_role"] == "ACADEMIC_SUPERVISOR"


def test_suspending_membership_revokes_access_on_next_login(platform, capsys) -> None:
    _onboard_supervisor(platform)
    base = [
        "--email",
        "orientador@universidade.br",
        "--workspace-slug",
        "nutev-doutorado",
        "--role",
        "ACADEMIC_SUPERVISOR",
        "--database",
        str(platform["database"]),
    ]
    _run_tool(base, capsys)

    code, payload = _run_tool([*base, "--status", "suspended"], capsys)
    assert code == 0
    assert payload["status"] == "membership_granted"
    assert payload["membership_status"] == "suspended"

    principal = platform["logins"].login(
        "orientador@universidade.br", SUPERVISOR_PASSWORD
    ).session.principal
    assert principal.membership_for(platform["workspace"].id) is None
    with pytest.raises(PermissionError, match="workspace_access_denied"):
        platform["access"].list_projects(principal, platform["workspace"].id)


def test_grant_fails_closed_on_unknown_user_workspace_and_database(platform, capsys) -> None:
    _onboard_supervisor(platform)
    database = str(platform["database"])

    code, payload = _run_tool(
        ["--email", "ninguem@example.org", "--workspace-slug", "nutev-doutorado",
         "--role", "ACADEMIC_SUPERVISOR", "--database", database],
        capsys,
    )
    assert (code, payload["status"]) == (4, "user_not_found")

    code, payload = _run_tool(
        ["--email", "orientador@universidade.br", "--workspace-slug", "nao-existe",
         "--role", "ACADEMIC_SUPERVISOR", "--database", database],
        capsys,
    )
    assert (code, payload["status"]) == (6, "workspace_not_found")

    code, payload = _run_tool(
        ["--email", "nao-e-email", "--workspace-slug", "nutev-doutorado",
         "--role", "ACADEMIC_SUPERVISOR", "--database", database],
        capsys,
    )
    assert (code, payload["status"]) == (2, "invalid_email")

    code, payload = _run_tool(
        ["--email", "orientador@universidade.br", "--workspace-slug", "nutev-doutorado",
         "--role", "ACADEMIC_SUPERVISOR", "--database", str(platform["database"].parent / "absent.sqlite3")],
        capsys,
    )
    assert (code, payload["status"]) == (3, "database_missing")


def test_grant_refuses_disabled_identity(platform, capsys) -> None:
    supervisor = _onboard_supervisor(platform)
    platform["auth"].set_user_status(supervisor.id, "disabled")

    code, payload = _run_tool(
        ["--email", "orientador@universidade.br", "--workspace-slug", "nutev-doutorado",
         "--role", "ACADEMIC_SUPERVISOR", "--database", str(platform["database"])],
        capsys,
    )
    assert (code, payload["status"]) == (5, "user_not_active")


def test_grant_cannot_assign_workspace_owner(platform) -> None:
    assert "WORKSPACE_OWNER" not in grant_tool._ASSIGNABLE_ROLES
    with pytest.raises(SystemExit):
        grant_tool.main(
            ["--email", "orientador@universidade.br", "--workspace-slug", "nutev-doutorado",
             "--role", "WORKSPACE_OWNER", "--database", str(platform["database"])]
        )


def test_granted_supervisor_cannot_reach_another_workspace(platform, capsys) -> None:
    _onboard_supervisor(platform)
    _run_tool(
        ["--email", "orientador@universidade.br", "--workspace-slug", "nutev-doutorado",
         "--role", "ACADEMIC_SUPERVISOR", "--database", str(platform["database"])],
        capsys,
    )
    other_owner = platform["auth"].provision_user(
        email="outro@example.org",
        display_name="Outro",
        password="another sufficiently long password",
    )
    foreign = platform["access"].provision_workspace(
        owner_user_id=other_owner.id,
        name="Outro Lab",
        slug="outro-lab",
    )
    principal = platform["logins"].login(
        "orientador@universidade.br", SUPERVISOR_PASSWORD
    ).session.principal

    assert principal.membership_for(foreign.id) is None
    assert not platform["access"].confirm_project_access(
        principal,
        workspace_id=foreign.id,
        project_id=platform["project"].id,
    )
    with pytest.raises(PermissionError):
        platform["access"].list_projects(principal, foreign.id)
