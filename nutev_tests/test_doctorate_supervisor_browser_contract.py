"""Contract for the two-actor doctorate browser regression.

The browser run itself needs Chromium and lives in CI. These tests guard the parts that can
go quietly wrong without it: that the fixture stays offline and disposable, that the run
actually exercises both actors, and that it proves the supervisor boundary at the endpoints
rather than by the absence of buttons.
"""
from __future__ import annotations

import ast
from pathlib import Path

import yaml

from nutev.tenancy import (
    Principal,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    WorkspaceRole,
)
from nutev.tenancy.permissions import (
    AuthorizationContext,
    Permission,
    PermissionService,
)

from tools.doctorate_supervisor_fixture import seed

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (ROOT / "tools" / "doctorate_supervisor_fixture.py").read_text(encoding="utf-8")
RUNNER = (ROOT / "tools" / "run_doctorate_supervisor_browser.py").read_text(encoding="utf-8")


def test_fixture_is_offline_disposable_and_creates_no_scientific_state() -> None:
    assert "NUTEV_DISABLE_NETWORK" in FIXTURE
    assert "'NUTEV_ENVIRONMENT': \"test\"" in FIXTURE or '"NUTEV_ENVIRONMENT": "test"' in FIXTURE
    assert "tempfile.TemporaryDirectory" in FIXTURE
    assert "fixture-only-not-production" in FIXTURE

    # Disposable identities only: never a real person's address.
    assert "@example.invalid" in FIXTURE
    for invented in ("caio", "willian@", "reis@"):
        assert invented not in FIXTURE.casefold(), "the fixture must not invent a real identity"

    # It provisions tenancy, not science. Checked against what the code calls rather than
    # against the words it uses: the module names PRESS and PRISMA precisely to disclaim them.
    called = {
        node.func.attr
        for node in ast.walk(ast.parse(FIXTURE))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert {"provision_user", "provision_workspace", "create_project", "add_or_update_member"} <= called
    for mutator in (
        "record_press",
        "authorize_gf10",
        "freeze_queries",
        "run_search",
        "create_round",
        "save_adjudication",
        "finalize_adjudication",
        "bind_legacy",
    ):
        assert mutator not in called, f"the fixture must not call {mutator}"


def test_fixture_grants_the_supervisor_read_only_authority(tmp_path: Path) -> None:
    """Guard the guard: if the seed stopped granting the role, the browser run would be vacuous."""
    data = seed(tmp_path)
    store = SQLiteWorkspaceProjectStore(Path(data["database"]))
    access = WorkspaceProjectService(store)
    supervisor = data["supervisor"]

    membership = store.active_membership(supervisor["user_id"], supervisor["workspace_id"])
    assert membership is not None
    assert membership.role is WorkspaceRole.ACADEMIC_SUPERVISOR

    principal = Principal(
        user_id=supervisor["user_id"],
        workspace_memberships=tuple(access.memberships_for_user(supervisor["user_id"])),
        global_roles=frozenset(),
        session_id="ses_" + "0" * 32,
    )
    context = access.authorization_context(
        principal,
        workspace_id=supervisor["workspace_id"],
        project_id=supervisor["project_id"],
    )
    permissions = PermissionService()

    for allowed in (
        Permission.APPLICATION_READ,
        Permission.SEARCH_HISTORY_READ,
        Permission.EVIDENCE_LIBRARY_READ,
        Permission.FULL_TEXT_ACCESS_READ,
        Permission.PROJECT_BANK_READ,
        Permission.HUMAN_REVIEW_READ,
        Permission.PROJECT_AUDIT_READ,
    ):
        assert permissions.can(principal, allowed, context=context), allowed

    for denied in (
        Permission.SEARCH_RUN,
        Permission.SCREEN,
        Permission.EXTRACT,
        Permission.ADJUDICATE,
        Permission.HUMAN_REVIEW_MANAGE,
        Permission.MEMBERS_MANAGE,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_DELETE,
        Permission.APPLICATION_MANAGE,
        Permission.EVIDENCE_LIBRARY_WRITE,
    ):
        assert not permissions.can(principal, denied, context=context), denied

    # The supervisor holds no global role, so supervision is never infrastructure authority.
    assert not principal.global_roles
    assert not permissions.can(
        principal,
        Permission.PLATFORM_INFRA_MANAGE,
        context=AuthorizationContext(workspace_id=supervisor["workspace_id"]),
    )

    # A foreign workspace exists for the death tests and the supervisor is not in it.
    assert data["outsider"]["workspace_id"] != supervisor["workspace_id"]
    assert store.active_membership(supervisor["user_id"], data["outsider"]["workspace_id"]) is None


def test_runner_exercises_both_actors_and_probes_endpoints_directly() -> None:
    for actor_step in (
        "_run_owner",
        "_run_supervisor",
        "owner_manages_members_without_ownership_transfer",
        "supervisor_forbidden_endpoints_refuse_directly",
        "supervisor_cannot_select_a_foreign_workspace",
        "supervisor_permitted_reads_still_succeed",
    ):
        assert actor_step in RUNNER, f"the browser run must cover {actor_step}"

    # Hidden buttons are not the proof; the endpoints are.
    for path in ("/api/workspace/members", "/api/workspace/members/status", "/api/application"):
        assert path in RUNNER
    assert 'assert result["status"] != 200' in RUNNER

    # And the gate panel must never be accepted as open.
    assert "no Article 1 gate may render as open" in RUNNER


def test_two_actor_regression_runs_in_the_pilot_browser_workflow() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/predeploy-browser-e2e.yml").read_text(encoding="utf-8")
    )
    steps = workflow["jobs"]["pilot-closeout"]["steps"]
    commands = " ".join(str(step.get("run") or "") for step in steps)
    assert "tools/run_doctorate_supervisor_browser.py" in commands
