"""Contract for the doctorate Article 1 provisioning command.

The command opens the workspace for the first time so an operator does not hand-write Python
against the production database. It must stay idempotent, refuse to invent identities or
ownership, and leave every scientific gate exactly where it found it.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from argon2 import PasswordHasher
import pytest

from nutev.tenancy import (
    ApplicationService,
    Principal,
    SCOPING_REVIEW,
    SQLiteApplicationStore,
    SQLiteAuthProvider,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    WorkspaceRole,
    initialize_platform_database,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "provision_doctorate_article1.py"
SPEC = importlib.util.spec_from_file_location("provision_doctorate_article1", MODULE_PATH)
assert SPEC and SPEC.loader
provision = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = provision
SPEC.loader.exec_module(provision)

OWNER_EMAIL = "responsavel@example.org"
OWNER_PASSWORD = "uma senha suficientemente longa do responsavel"


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


@pytest.fixture()
def database(tmp_path: Path) -> Path:
    path = tmp_path / "auth.sqlite3"
    initialize_platform_database(path)
    SQLiteAuthProvider(path, password_hasher=_fast_hasher()).provision_user(
        email=OWNER_EMAIL, display_name="Responsavel", password=OWNER_PASSWORD
    )
    return path


def _run(database: Path, capsys, *extra: str) -> tuple[int, dict]:
    code = provision.main(
        [
            "--owner-email",
            OWNER_EMAIL,
            "--workspace-name",
            "Doutorado",
            "--workspace-slug",
            "doutorado",
            "--project-name",
            "Artigo 1",
            "--project-slug",
            "artigo-1",
            "--project-type",
            "review",
            "--database",
            str(database),
            *extra,
        ]
    )
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    return code, payload


def test_provisioning_creates_the_workspace_project_and_scoping_application(database, capsys) -> None:
    code, payload = _run(database, capsys, "--article1-assembly")

    assert code == 0
    assert payload["status"] == "provisioned"
    assert payload["workspace_created"] is True
    assert payload["project_created"] is True
    assert payload["application_created"] is True
    assert payload["application_type"] == SCOPING_REVIEW
    assert payload["template_id"] == SCOPING_REVIEW

    # It provisions access, never identity, authority or scientific approval.
    assert payload["user_created"] is False
    assert payload["password_created"] is False
    assert payload["global_role_granted"] is False
    assert payload["scientific_state_modified"] is False
    assert payload["scientific_approval_created"] is False

    assert payload["article1_assembly_configured"] is True
    assert payload["d132_config_version"] == "d132-v1"

    # Historical ownership binding is reported as a remaining human step, never performed here.
    assert payload["historical_binding_activated"] is False
    assert any("NUTEV_A1_WORKSPACE_ID" in step for step in payload["next_steps"])

    store = SQLiteWorkspaceProjectStore(database)
    workspace = store.get_workspace(payload["workspace_id"])
    assert workspace is not None
    assert store.active_membership(workspace.owner_user_id, workspace.id).role is WorkspaceRole.WORKSPACE_OWNER

    # The owner is the only member: provisioning grants nobody else access.
    assert len(store.list_memberships(workspace.id)) == 1
    assert payload["membership_granted_to_others"] is False


def test_provisioning_repairs_missing_d132_binding_without_overwriting_private_configuration(
    database, capsys
) -> None:
    _, first = _run(database, capsys, "--article1-assembly")

    store = SQLiteWorkspaceProjectStore(database)
    access = WorkspaceProjectService(store)
    applications = ApplicationService(SQLiteApplicationStore(database), access)
    principal = Principal(
        user_id=store.get_workspace(first["workspace_id"]).owner_user_id,
        workspace_memberships=tuple(access.memberships_for_user(store.get_workspace(first["workspace_id"]).owner_user_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )
    applications.configure(
        principal,
        workspace_id=first["workspace_id"],
        project_id=first["project_id"],
        template_id=SCOPING_REVIEW,
        configuration={"assembly_id": "WILLIAN_DOCTORATE_A1", "operator_note": "private"},
    )

    code, repaired = _run(database, capsys, "--article1-assembly")

    assert code == 0
    assert repaired["status"] == "provisioned"
    assert repaired["changed"] is True
    assert repaired["application_created"] is False
    assert repaired["application_updated"] is True
    assert repaired["workspace_id"] == first["workspace_id"]
    assert repaired["project_id"] == first["project_id"]
    assert repaired["d132_config_version"] == "d132-v1"

    current = applications.get(
        principal, workspace_id=first["workspace_id"], project_id=first["project_id"]
    )
    configuration = current.descriptor()["configuration"]
    assert configuration["assembly_id"] == "WILLIAN_DOCTORATE_A1"
    assert configuration["d132_config_version"] == "d132-v1"
    assert configuration["operator_note"] == "private", "repair must preserve private config"

    code, idempotent = _run(database, capsys, "--article1-assembly")
    assert code == 0
    assert idempotent["status"] == "already_provisioned"
    assert idempotent["changed"] is False
    assert idempotent["application_updated"] is False


def test_provisioning_refuses_conflicting_article1_binding_without_overwrite(database, capsys) -> None:
    _, first = _run(database, capsys)

    store = SQLiteWorkspaceProjectStore(database)
    access = WorkspaceProjectService(store)
    applications = ApplicationService(SQLiteApplicationStore(database), access)
    owner_id = store.get_workspace(first["workspace_id"]).owner_user_id
    principal = Principal(
        user_id=owner_id,
        workspace_memberships=tuple(access.memberships_for_user(owner_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )
    applications.configure(
        principal,
        workspace_id=first["workspace_id"],
        project_id=first["project_id"],
        template_id=SCOPING_REVIEW,
        configuration={
            "assembly_id": "SOME_OTHER_ASSEMBLY",
            "d132_config_version": "d132-v1",
            "operator_note": "keep-me",
        },
    )

    code, payload = _run(database, capsys, "--article1-assembly")

    assert code == 10
    assert payload["status"] == "application_binding_conflict"
    assert payload["changed"] is False
    assert payload["conflicting_keys"] == ["assembly_id"]

    current = applications.get(
        principal, workspace_id=first["workspace_id"], project_id=first["project_id"]
    )
    configuration = current.descriptor()["configuration"]
    assert configuration["assembly_id"] == "SOME_OTHER_ASSEMBLY"
    assert configuration["operator_note"] == "keep-me"


def test_the_article1_assembly_tag_is_opt_in(database, capsys) -> None:
    """The assembly id is configuration. Without the flag the command does not write it."""
    code, payload = _run(database, capsys)
    assert code == 0

    store = SQLiteWorkspaceProjectStore(database)
    access = WorkspaceProjectService(store)
    applications = ApplicationService(SQLiteApplicationStore(database), access)
    owner_id = store.get_workspace(payload["workspace_id"]).owner_user_id
    principal = Principal(
        user_id=owner_id,
        workspace_memberships=tuple(access.memberships_for_user(owner_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )
    current = applications.get(
        principal, workspace_id=payload["workspace_id"], project_id=payload["project_id"]
    )
    assert "assembly_id" not in current.descriptor()["configuration"]


def test_provisioning_fails_closed_on_unknown_owner_and_missing_database(tmp_path, database, capsys) -> None:
    code = provision.main(
        [
            "--owner-email",
            "ninguem@example.org",
            "--workspace-name",
            "X",
            "--workspace-slug",
            "x",
            "--project-name",
            "Y",
            "--project-slug",
            "y",
            "--database",
            str(database),
        ]
    )
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert code == 4
    assert payload["status"] == "owner_not_found"
    assert SQLiteWorkspaceProjectStore(database).list_projects(new_opaque_id("workspace")) == ()

    code = provision.main(
        [
            "--owner-email",
            OWNER_EMAIL,
            "--workspace-name",
            "X",
            "--workspace-slug",
            "x",
            "--project-name",
            "Y",
            "--project-slug",
            "y",
            "--database",
            str(tmp_path / "absent.sqlite3"),
        ]
    )
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert code == 3
    assert payload["status"] == "database_missing"


def test_provisioning_refuses_a_workspace_owned_by_another_identity(database, capsys) -> None:
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    other = auth.provision_user(
        email="outro@example.org", display_name="Outro", password="outra senha suficientemente longa"
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    existing = access.provision_workspace(owner_user_id=other.id, name="Doutorado", slug="doutorado")

    code, payload = _run(database, capsys)

    assert code == 7
    assert payload["status"] == "workspace_owned_by_another_identity"
    assert payload["changed"] is False
    assert SQLiteWorkspaceProjectStore(database).get_workspace(existing.id).owner_user_id == other.id


def test_command_leaves_the_article1_gate_state_untouched(database, capsys) -> None:
    master_path = ROOT / "config/nutev/article1_search_master_v1.json"
    before = json.loads(master_path.read_text(encoding="utf-8"))

    _run(database, capsys, "--article1-assembly")

    after = json.loads(master_path.read_text(encoding="utf-8"))
    assert after == before
    formal = after["formal_search"]
    assert formal["press_status"] == "NOT_YET_RECORDED_AS_PASS"
    assert formal["gf10_authorized"] is False
    assert formal["query_freeze_complete"] is False
    assert formal["formal_provider_search_executed"] is False
    assert formal["prisma_search_event_emitted"] is False
