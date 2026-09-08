from __future__ import annotations

import pytest

from nutev.tenancy import (
    AuthorizationContext,
    GlobalRole,
    Membership,
    MembershipStatus,
    Permission,
    PermissionDenied,
    PermissionScope,
    PermissionService,
    Principal,
    Project,
    ResearchApplication,
    User,
    Workspace,
    WorkspaceRole,
    new_opaque_id,
)


def _ids() -> tuple[str, str, str, str, str]:
    return (
        new_opaque_id("user"),
        new_opaque_id("workspace"),
        new_opaque_id("project"),
        new_opaque_id("application"),
        new_opaque_id("session"),
    )


def _principal(role: WorkspaceRole, *, global_roles=frozenset(), status=MembershipStatus.ACTIVE):
    user_id, workspace_id, project_id, _app_id, session_id = _ids()
    membership = Membership(
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
        status=status,
    )
    return (
        Principal(
            user_id=user_id,
            workspace_memberships=(membership,),
            global_roles=frozenset(global_roles),
            session_id=session_id,
        ),
        workspace_id,
        project_id,
    )


def test_opaque_identity_contracts_and_models() -> None:
    user_id, workspace_id, project_id, app_id, _session_id = _ids()
    user = User(id=user_id, email="researcher@example.org", display_name="Researcher")
    workspace = Workspace(
        id=workspace_id,
        name="Evidence Lab",
        slug="evidence-lab",
        owner_user_id=user.id,
    )
    project = Project(
        id=project_id,
        workspace_id=workspace.id,
        name="Review A",
        slug="review-a",
        project_type="review",
        created_by=user.id,
    )
    application = ResearchApplication(
        id=app_id,
        project_id=project.id,
        application_type="SCOPING_REVIEW",
        template_id=None,
        config_version="1",
    )

    assert user.id.startswith("usr_")
    assert workspace.id.startswith("wsp_")
    assert project.id.startswith("prj_")
    assert application.id.startswith("app_")
    assert len({new_opaque_id("user") for _ in range(20)}) == 20


def test_principal_rejects_membership_for_another_user() -> None:
    user_id, workspace_id, _project_id, _app_id, session_id = _ids()
    foreign_user = new_opaque_id("user")
    membership = Membership(
        workspace_id=workspace_id,
        user_id=foreign_user,
        role=WorkspaceRole.RESEARCHER,
    )
    with pytest.raises(ValueError, match="another user"):
        Principal(
            user_id=user_id,
            workspace_memberships=(membership,),
            global_roles=frozenset(),
            session_id=session_id,
        )


def test_platform_admin_is_not_private_scientific_data_bypass() -> None:
    principal, workspace_id, project_id = _principal(
        WorkspaceRole.VIEWER,
        global_roles={GlobalRole.PLATFORM_ADMIN},
    )
    service = PermissionService()

    assert service.can(principal, Permission.PLATFORM_INFRA_MANAGE)
    assert not service.can(
        principal,
        Permission.SCREEN,
        context=AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
        ),
    )


def test_cross_workspace_access_fails_closed() -> None:
    principal, _workspace_id, project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    service = PermissionService()
    foreign_workspace = new_opaque_id("workspace")

    decision = service.decide(
        principal,
        Permission.PROJECT_BANK_READ,
        context=AuthorizationContext(
            workspace_id=foreign_workspace,
            project_id=project_id,
            project_access_confirmed=True,
        ),
    )
    assert not decision.allowed
    assert decision.reason == "active_membership_required"


def test_inactive_membership_has_no_permissions() -> None:
    principal, workspace_id, _project_id = _principal(
        WorkspaceRole.WORKSPACE_OWNER,
        status=MembershipStatus.REMOVED,
    )
    decision = PermissionService().decide(
        principal,
        Permission.SEARCH_RUN,
        context=AuthorizationContext(workspace_id=workspace_id),
    )
    assert not decision.allowed
    assert decision.reason == "active_membership_required"


@pytest.mark.parametrize(
    ("role", "permission", "allowed"),
    [
        (WorkspaceRole.WORKSPACE_OWNER, Permission.WORKSPACE_SETTINGS_MANAGE, True),
        (WorkspaceRole.WORKSPACE_ADMIN, Permission.MEMBERS_MANAGE, True),
        (WorkspaceRole.RESEARCHER, Permission.SEARCH_RUN, True),
        (WorkspaceRole.REVIEWER, Permission.SEARCH_RUN, False),
        (WorkspaceRole.VIEWER, Permission.SEARCH_RUN, False),
        (WorkspaceRole.GUEST_REVIEWER, Permission.PROJECT_BANK_READ, False),
        (WorkspaceRole.RESEARCHER, Permission.PROJECT_DELETE, False),
        (WorkspaceRole.WORKSPACE_ADMIN, Permission.WORKSPACE_TRANSFER_OWNERSHIP, False),
        (WorkspaceRole.WORKSPACE_OWNER, Permission.WORKSPACE_TRANSFER_OWNERSHIP, True),
        (WorkspaceRole.WORKSPACE_ADMIN, Permission.WORKSPACE_DELETE, False),
    ],
)
def test_minimum_role_matrix(role: WorkspaceRole, permission: Permission, allowed: bool) -> None:
    principal, workspace_id, _project_id = _principal(role)
    result = PermissionService().can(
        principal,
        permission,
        context=AuthorizationContext(workspace_id=workspace_id),
    )
    assert result is allowed


def test_researcher_conditional_permissions_require_explicit_policy() -> None:
    principal, workspace_id, _project_id = _principal(WorkspaceRole.RESEARCHER)
    service = PermissionService()
    base = AuthorizationContext(workspace_id=workspace_id)

    assert not service.can(principal, Permission.PROJECT_CREATE, context=base)
    assert service.can(
        principal,
        Permission.PROJECT_CREATE,
        context=AuthorizationContext(
            workspace_id=workspace_id,
            policy_grants=frozenset({Permission.PROJECT_CREATE}),
        ),
    )


def test_project_permission_requires_separate_project_access_confirmation() -> None:
    principal, workspace_id, project_id = _principal(WorkspaceRole.RESEARCHER)
    service = PermissionService()

    denied = service.decide(
        principal,
        Permission.SCREEN,
        context=AuthorizationContext(workspace_id=workspace_id, project_id=project_id),
    )
    allowed = service.decide(
        principal,
        Permission.SCREEN,
        context=AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
        ),
    )
    assert not denied.allowed
    assert denied.reason == "project_access_not_confirmed"
    assert allowed.allowed
    assert allowed.scope is PermissionScope.FULL


def test_reviewer_is_assignment_scoped() -> None:
    service = PermissionService()
    principal, workspace_id, project_id = _principal(WorkspaceRole.REVIEWER)
    unassigned = AuthorizationContext(
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        assigned=False,
    )
    assigned = AuthorizationContext(
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        assigned=True,
    )
    assert not service.can(principal, Permission.SCREEN, context=unassigned)
    decision = service.decide(principal, Permission.SCREEN, context=assigned)
    assert decision.allowed
    assert decision.scope is PermissionScope.ASSIGNED


def test_guest_reviewer_contract_is_assignment_only_without_implying_account_model() -> None:
    from nutev.tenancy import ROLE_PERMISSIONS

    assert ROLE_PERMISSIONS[WorkspaceRole.GUEST_REVIEWER][Permission.SCREEN].scope is PermissionScope.ASSIGNED
    assert ROLE_PERMISSIONS[WorkspaceRole.GUEST_REVIEWER][Permission.EXTRACT].scope is PermissionScope.ASSIGNED
    assert Permission.PROJECT_BANK_READ not in ROLE_PERMISSIONS[WorkspaceRole.GUEST_REVIEWER]


def test_reviewer_bank_access_is_limited_to_assigned_context() -> None:
    principal, workspace_id, project_id = _principal(WorkspaceRole.REVIEWER)
    service = PermissionService()
    assert not service.can(
        principal,
        Permission.PROJECT_BANK_READ,
        context=AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
        ),
    )
    assert service.can(
        principal,
        Permission.PROJECT_BANK_READ,
        context=AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            assigned=True,
        ),
    )


def test_search_saved_into_project_requires_project_access_confirmation() -> None:
    principal, workspace_id, project_id = _principal(WorkspaceRole.RESEARCHER)
    service = PermissionService()

    assert service.can(
        principal,
        Permission.SEARCH_RUN,
        context=AuthorizationContext(workspace_id=workspace_id),
    )
    assert not service.can(
        principal,
        Permission.SEARCH_RUN,
        context=AuthorizationContext(workspace_id=workspace_id, project_id=project_id),
    )
    assert service.can(
        principal,
        Permission.SEARCH_RUN,
        context=AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
        ),
    )


def test_require_raises_on_denied_permission() -> None:
    principal, workspace_id, _project_id = _principal(WorkspaceRole.VIEWER)
    with pytest.raises(PermissionDenied, match="search.run"):
        PermissionService().require(
            principal,
            Permission.SEARCH_RUN,
            context=AuthorizationContext(workspace_id=workspace_id),
        )


def test_owner_workspace_delete_is_policy_gated() -> None:
    principal, workspace_id, _project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    service = PermissionService()
    assert not service.can(
        principal,
        Permission.WORKSPACE_DELETE,
        context=AuthorizationContext(workspace_id=workspace_id),
    )
    assert service.can(
        principal,
        Permission.WORKSPACE_DELETE,
        context=AuthorizationContext(
            workspace_id=workspace_id,
            policy_grants=frozenset({Permission.WORKSPACE_DELETE}),
        ),
    )
