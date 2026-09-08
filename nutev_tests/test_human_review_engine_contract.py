from __future__ import annotations

from pathlib import Path

from nutev.tenancy import AuthorizationContext, Permission, PermissionService, Principal, WorkspaceRole
from nutev.tenancy import Membership, new_opaque_id

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "src" / "nutev" / "review" / "engine.py"
LEGACY = ROOT / "apps" / "nutev-web" / "validation_server.py"


def _principal(role: WorkspaceRole) -> tuple[Principal, str, str]:
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
            global_roles=frozenset(),
            session_id=new_opaque_id("session"),
        ),
        workspace_id,
        project_id,
    )


def test_engine_is_application_agnostic_and_does_not_import_legacy_validation() -> None:
    source = ENGINE.read_text(encoding="utf-8").casefold()
    assert "article1" not in source
    assert "article 1" not in source
    assert "article2" not in source
    assert "article 2" not in source
    assert "d-132" not in source
    assert "validation_server" not in source
    assert "validation.sqlite3" not in source
    assert "nutev_rank" not in source
    assert "machine_relevance" not in source


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
