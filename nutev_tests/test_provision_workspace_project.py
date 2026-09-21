"""Provisioning contract for the first workspace of a hosted deployment.

A production inspect returned `{"account": null, "memberships": [], "workspaces": []}`
— tenancy state exists but nothing has been provisioned in it. Without a workspace
no membership can be granted, so this step is what unblocks supervisor onboarding.

Because it is the first write into an empty platform, its refusals matter more than
its successes: it must never invent an owner, never adopt somebody else's workspace,
and never leave scientific state behind.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

from argon2 import PasswordHasher
import pytest

from nutev.tenancy import (
    SQLiteAuthProvider,
    SQLiteWorkspaceProjectStore,
    WorkspaceRole,
    initialize_platform_database,
)

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "provision_workspace_project.py"
SPEC = importlib.util.spec_from_file_location("provision_workspace_project", MODULE_PATH)
assert SPEC and SPEC.loader
provision = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = provision
SPEC.loader.exec_module(provision)

OWNER_EMAIL = "owner@example.org"
OWNER_PASSWORD = "a sufficiently long owner password"


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)


def _run(argv: list[str], capsys) -> tuple[int, dict]:
    code = provision.main(argv)
    return code, json.loads(capsys.readouterr().out.strip().splitlines()[-1])


@pytest.fixture()
def empty_platform(tmp_path: Path) -> Path:
    """A bootstrapped but wholly unprovisioned database, as production was."""

    database = tmp_path / "auth.sqlite3"
    initialize_platform_database(database)
    return database


@pytest.fixture()
def platform_with_owner(empty_platform: Path) -> Path:
    SQLiteAuthProvider(empty_platform, password_hasher=_fast_hasher()).provision_user(
        email=OWNER_EMAIL,
        display_name="Owner",
        password=OWNER_PASSWORD,
    )
    return empty_platform


def _argv(database: Path, **overrides: str) -> list[str]:
    values = {
        "--owner-email": OWNER_EMAIL,
        "--workspace-name": "NutEV Doutorado",
        "--workspace-slug": "nutev-doutorado",
        "--project-name": "Artigo 1",
        "--project-slug": "artigo-1",
        "--database": str(database),
    }
    values.update(overrides)
    return [item for pair in values.items() for item in pair]


def test_refuses_on_an_empty_platform_and_says_no_account_exists_at_all(
    empty_platform: Path,
    capsys,
) -> None:
    """The distinction that matters: nothing provisioned vs. the wrong address."""

    code, payload = _run(_argv(empty_platform), capsys)

    assert code == 4
    assert payload["status"] == "owner_not_found"
    assert payload["accounts_on_platform"] == 0
    assert "no account has been provisioned at all" in payload["hint"].casefold()
    assert payload["changed"] is False

    with sqlite3.connect(empty_platform) as connection:
        assert connection.execute("SELECT COUNT(*) FROM platform_workspaces").fetchone()[0] == 0


def test_refusal_distinguishes_a_wrong_address_from_an_empty_platform(
    platform_with_owner: Path,
    capsys,
) -> None:
    code, payload = _run(
        _argv(platform_with_owner, **{"--owner-email": "outro@example.org"}),
        capsys,
    )

    assert code == 4
    assert payload["accounts_on_platform"] == 1
    assert "not under this address" in payload["hint"]
    # No other person's address may be disclosed in the receipt.
    assert OWNER_EMAIL not in json.dumps(payload)


def test_creates_workspace_project_and_the_owner_membership(
    platform_with_owner: Path,
    capsys,
) -> None:
    code, payload = _run(_argv(platform_with_owner), capsys)

    assert code == 0
    assert payload["status"] == "provisioned"
    assert payload["changed"] is True
    assert payload["workspace"]["slug"] == "nutev-doutorado"
    assert payload["workspace"]["created_now"] is True
    assert payload["project"]["slug"] == "artigo-1"
    assert payload["project"]["created_now"] is True
    assert payload["user_created"] is False
    assert payload["research_application_configured"] is False
    assert payload["scientific_state_modified"] is False

    store = SQLiteWorkspaceProjectStore(platform_with_owner)
    memberships = store.memberships_for_user(payload["owner"]["user_id"])
    assert [m.role for m in memberships] == [WorkspaceRole.WORKSPACE_OWNER]
    assert memberships[0].workspace_id == payload["workspace"]["id"]


def test_running_twice_changes_nothing(platform_with_owner: Path, capsys) -> None:
    first = _run(_argv(platform_with_owner), capsys)
    assert first[0] == 0 and first[1]["changed"] is True

    code, payload = _run(_argv(platform_with_owner), capsys)

    assert code == 0
    assert payload["status"] == "already_present"
    assert payload["changed"] is False
    assert payload["workspace"]["created_now"] is False
    assert payload["project"]["created_now"] is False
    assert payload["workspace"]["id"] == first[1]["workspace"]["id"]
    assert payload["project"]["id"] == first[1]["project"]["id"]

    with sqlite3.connect(platform_with_owner) as connection:
        assert connection.execute("SELECT COUNT(*) FROM platform_workspaces").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM platform_projects").fetchone()[0] == 1


def test_never_adopts_a_workspace_owned_by_another_identity(
    platform_with_owner: Path,
    capsys,
) -> None:
    """Reusing a slug must not hand somebody else's projects to this owner."""

    _run(_argv(platform_with_owner), capsys)
    other = SQLiteAuthProvider(
        platform_with_owner, password_hasher=_fast_hasher()
    ).provision_user(
        email="outro@example.org",
        display_name="Outro",
        password="another sufficiently long password",
    )

    code, payload = _run(
        _argv(platform_with_owner, **{"--owner-email": "outro@example.org"}),
        capsys,
    )

    assert code == 6
    assert payload["status"] == "workspace_slug_owned_by_another_identity"
    assert payload["changed"] is False

    store = SQLiteWorkspaceProjectStore(platform_with_owner)
    assert store.memberships_for_user(other.id) == ()


def test_refuses_a_disabled_owner(platform_with_owner: Path, capsys) -> None:
    auth = SQLiteAuthProvider(platform_with_owner, password_hasher=_fast_hasher())
    subject = auth.authenticate(OWNER_EMAIL, OWNER_PASSWORD)
    assert subject is not None
    auth.set_user_status(subject.user.id, "disabled")

    code, payload = _run(_argv(platform_with_owner), capsys)

    assert code == 5
    assert payload["status"] == "owner_not_active"
    with sqlite3.connect(platform_with_owner) as connection:
        assert connection.execute("SELECT COUNT(*) FROM platform_workspaces").fetchone()[0] == 0


def test_workspace_can_be_created_without_a_project(
    platform_with_owner: Path,
    capsys,
) -> None:
    code, payload = _run(
        [
            "--owner-email", OWNER_EMAIL,
            "--workspace-name", "Somente Workspace",
            "--workspace-slug", "somente-workspace",
            "--database", str(platform_with_owner),
        ],
        capsys,
    )

    assert code == 0
    assert payload["project"] is None
    with sqlite3.connect(platform_with_owner) as connection:
        assert connection.execute("SELECT COUNT(*) FROM platform_projects").fetchone()[0] == 0


def test_project_name_and_slug_must_be_given_together(
    platform_with_owner: Path,
    capsys,
) -> None:
    code, payload = _run(
        [
            "--owner-email", OWNER_EMAIL,
            "--workspace-name", "Parcial",
            "--workspace-slug", "parcial",
            "--project-name", "Sem slug",
            "--database", str(platform_with_owner),
        ],
        capsys,
    )

    assert code == 2
    assert payload["status"] == "project_name_and_slug_must_be_given_together"
    with sqlite3.connect(platform_with_owner) as connection:
        assert connection.execute("SELECT COUNT(*) FROM platform_workspaces").fetchone()[0] == 0


def test_refuses_a_malformed_slug_without_creating_anything(
    platform_with_owner: Path,
    capsys,
) -> None:
    code, payload = _run(
        _argv(platform_with_owner, **{"--workspace-slug": "Slug Invalido!"}),
        capsys,
    )

    assert code == 6
    assert payload["status"] == "workspace_refused"
    assert "lowercase" in payload["reason"]
    with sqlite3.connect(platform_with_owner) as connection:
        assert connection.execute("SELECT COUNT(*) FROM platform_workspaces").fetchone()[0] == 0


def test_missing_database_is_refused_rather_than_created(tmp_path: Path, capsys) -> None:
    absent = tmp_path / "nowhere.sqlite3"
    code, payload = _run(_argv(absent), capsys)

    assert code == 3
    assert payload["status"] == "database_missing"
    assert not absent.exists()
