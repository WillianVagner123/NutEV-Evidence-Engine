from __future__ import annotations

from pathlib import Path

from nutev.tenancy import (
    AuthorizationContext,
    GlobalRole,
    Membership,
    Permission,
    PermissionService,
    Principal,
    WorkspaceRole,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "src" / "nutev" / "review" / "engine.py"
LEGACY = ROOT / "apps" / "nutev-web" / "validation_server.py"


def _principal(
    role: WorkspaceRole,
    *,
    global_roles: frozenset[GlobalRole] = frozenset(),
) -> tuple[Principal, str, str]:
    user_id = new_opaque_id("user")
    workspace_id = new_opaque_id("workspace")
    project_id = new_opaque_id("project")
    return (
        Principal(
            user_id=user_id,
            workspace_memberships=(
                Membership(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role=role,
                ),
            ),
            global_roles=global_roles,
            session_id=new_opaque_id("session"),
        ),
        workspace_id,
        project_id,
    )


def test_engine_is_application_agnostic_and_does_not_import_legacy_validation() -> None:
    source = ENGINE.read_text(encoding="utf-8").casefold()

    # Explanatory docstrings may name examples to state the boundary. What is forbidden
    # in the reusable engine is concrete first-party configuration, paths, targets or
    # application-specific implementation symbols.
    forbidden_concrete_contracts = (
        "article1_project",
        "article2_project",
        "doctorate_workspace",
        "agent_context/article1",
        "scientific/review_routes",
        "article1_press",
        "article1_search_master",
        "d132_",
        "validation_server",
        "validation.sqlite3",
        "nutev_rank",
        "nutev_score",
        "machine_relevance",
        "r1_decision",
    )
    for forbidden in forbidden_concrete_contracts:
        assert forbidden not in source


def test_legacy_validation_remains_present_and_is_not_replaced_by_pr8() -> None:
    source = LEGACY.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS validation_rounds" in source
    assert "CREATE TABLE IF NOT EXISTS validation_reviewers" in source
    assert "CREATE TABLE IF NOT EXISTS validation_assignments" in source
    assert "def reviewer_payload(" in source
    assert "def save_decision(" in source
    assert "def submit_reviewer(" in source


def test_human_review_permissions_are_centralized_and_assigned_for_reviewer() -> None:
    service = PermissionService()
    reviewer, workspace_id, project_id = _principal(WorkspaceRole.REVIEWER)
    assigned = AuthorizationContext(
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        assigned=True,
    )
    unassigned = AuthorizationContext(
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        assigned=False,
    )
    assert service.can(reviewer, Permission.HUMAN_REVIEW_READ, context=assigned)
    assert not service.can(reviewer, Permission.HUMAN_REVIEW_READ, context=unassigned)
    assert not service.can(reviewer, Permission.HUMAN_REVIEW_MANAGE, context=assigned)


def test_owner_can_manage_review_but_viewer_cannot() -> None:
    service = PermissionService()
    owner, workspace_id, project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    viewer, viewer_workspace_id, viewer_project_id = _principal(WorkspaceRole.VIEWER)
    assert service.can(
        owner,
        Permission.HUMAN_REVIEW_MANAGE,
        context=AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
        ),
    )
    assert not service.can(
        viewer,
        Permission.HUMAN_REVIEW_MANAGE,
        context=AuthorizationContext(
            workspace_id=viewer_workspace_id,
            project_id=viewer_project_id,
            project_access_confirmed=True,
        ),
    )


def test_platform_admin_role_does_not_bypass_private_human_review_permissions() -> None:
    service = PermissionService()
    admin, workspace_id, project_id = _principal(
        WorkspaceRole.VIEWER,
        global_roles=frozenset({GlobalRole.PLATFORM_ADMIN}),
    )
    context = AuthorizationContext(
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
    )

    assert service.can(admin, Permission.PLATFORM_INFRA_MANAGE)
    assert not service.can(admin, Permission.HUMAN_REVIEW_MANAGE, context=context)
