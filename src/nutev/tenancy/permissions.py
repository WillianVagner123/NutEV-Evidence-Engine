from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .models import GlobalRole, Principal, WorkspaceRole, require_opaque_id


class Permission(StrEnum):
    PLATFORM_INFRA_MANAGE = "platform.infra.manage"
    WORKSPACE_SETTINGS_MANAGE = "workspace.settings.manage"
    MEMBERS_MANAGE = "workspace.members.manage"
    WORKSPACE_TRANSFER_OWNERSHIP = "workspace.ownership.transfer"
    WORKSPACE_DELETE = "workspace.delete"
    PROJECT_CREATE = "project.create"
    APPLICATION_READ = "application.read"
    APPLICATION_MANAGE = "application.manage"
    SEARCH_RUN = "search.run"
    SEARCH_HISTORY_READ = "search.history.read"
    EVIDENCE_LIBRARY_READ = "evidence_library.read"
    EVIDENCE_LIBRARY_WRITE = "evidence_library.write"
    FULL_TEXT_ACCESS_READ = "full_text_access.read"
    FULL_TEXT_ACCESS_MANAGE = "full_text_access.manage"
    PROJECT_BANK_READ = "project.bank.read"
    HUMAN_REVIEW_READ = "human_review.read"
    HUMAN_REVIEW_MANAGE = "human_review.manage"
    SCREEN = "project.screen"
    EXTRACT = "project.extract"
    ADJUDICATE = "project.adjudicate"
    EXPORT = "project.export"
    PROJECT_DELETE = "project.delete"


class PermissionScope(StrEnum):
    NONE = "none"
    FULL = "full"
    ASSIGNED = "assigned"


@dataclass(frozen=True, slots=True)
class PermissionRule:
    scope: PermissionScope
    policy_gated: bool = False


@dataclass(frozen=True, slots=True)
class AuthorizationContext:
    workspace_id: str | None = None
    project_id: str | None = None
    project_access_confirmed: bool = False
    assigned: bool = False
    policy_grants: frozenset[Permission] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class PermissionDecision:
    allowed: bool
    permission: Permission
    scope: PermissionScope = PermissionScope.NONE
    role: WorkspaceRole | GlobalRole | None = None
    reason: str = "denied"


class PermissionDenied(PermissionError):
    pass


_FULL = PermissionRule(PermissionScope.FULL)
_ASSIGNED = PermissionRule(PermissionScope.ASSIGNED)
_POLICY = PermissionRule(PermissionScope.FULL, policy_gated=True)

# Single source of truth for the minimum role matrix specified by the platform contract.
ROLE_PERMISSIONS: dict[WorkspaceRole, dict[Permission, PermissionRule]] = {
    WorkspaceRole.WORKSPACE_OWNER: {
        Permission.WORKSPACE_SETTINGS_MANAGE: _FULL,
        Permission.MEMBERS_MANAGE: _FULL,
        Permission.WORKSPACE_TRANSFER_OWNERSHIP: _FULL,
        Permission.WORKSPACE_DELETE: _POLICY,
        Permission.PROJECT_CREATE: _FULL,
        Permission.APPLICATION_READ: _FULL,
        Permission.APPLICATION_MANAGE: _FULL,
        Permission.SEARCH_RUN: _FULL,
        Permission.SEARCH_HISTORY_READ: _FULL,
        Permission.EVIDENCE_LIBRARY_READ: _FULL,
        Permission.EVIDENCE_LIBRARY_WRITE: _FULL,
        Permission.FULL_TEXT_ACCESS_READ: _FULL,
        Permission.FULL_TEXT_ACCESS_MANAGE: _FULL,
        Permission.PROJECT_BANK_READ: _FULL,
        Permission.HUMAN_REVIEW_READ: _FULL,
        Permission.HUMAN_REVIEW_MANAGE: _FULL,
        Permission.SCREEN: _FULL,
        Permission.EXTRACT: _FULL,
        Permission.ADJUDICATE: _FULL,
        Permission.EXPORT: _FULL,
        Permission.PROJECT_DELETE: _FULL,
    },
    WorkspaceRole.WORKSPACE_ADMIN: {
        Permission.WORKSPACE_SETTINGS_MANAGE: _FULL,
        Permission.MEMBERS_MANAGE: _FULL,
        Permission.PROJECT_CREATE: _FULL,
        Permission.APPLICATION_READ: _FULL,
        Permission.APPLICATION_MANAGE: _FULL,
        Permission.SEARCH_RUN: _FULL,
        Permission.SEARCH_HISTORY_READ: _FULL,
        Permission.EVIDENCE_LIBRARY_READ: _FULL,
        Permission.EVIDENCE_LIBRARY_WRITE: _FULL,
        Permission.FULL_TEXT_ACCESS_READ: _FULL,
        Permission.FULL_TEXT_ACCESS_MANAGE: _FULL,
        Permission.PROJECT_BANK_READ: _FULL,
        Permission.HUMAN_REVIEW_READ: _FULL,
        Permission.HUMAN_REVIEW_MANAGE: _FULL,
        Permission.SCREEN: _FULL,
        Permission.EXTRACT: _FULL,
        Permission.ADJUDICATE: _FULL,
        Permission.EXPORT: _FULL,
        Permission.PROJECT_DELETE: _POLICY,
    },
    WorkspaceRole.RESEARCHER: {
        Permission.PROJECT_CREATE: _POLICY,
        Permission.APPLICATION_READ: _FULL,
        Permission.APPLICATION_MANAGE: _FULL,
        Permission.SEARCH_RUN: _FULL,
        Permission.SEARCH_HISTORY_READ: _FULL,
        Permission.EVIDENCE_LIBRARY_READ: _FULL,
        Permission.EVIDENCE_LIBRARY_WRITE: _FULL,
        Permission.FULL_TEXT_ACCESS_READ: _FULL,
        Permission.FULL_TEXT_ACCESS_MANAGE: _FULL,
        Permission.PROJECT_BANK_READ: _FULL,
        Permission.HUMAN_REVIEW_READ: _FULL,
        Permission.HUMAN_REVIEW_MANAGE: _FULL,
        Permission.SCREEN: _FULL,
        Permission.EXTRACT: _FULL,
        Permission.ADJUDICATE: _POLICY,
        Permission.EXPORT: _POLICY,
    },
    WorkspaceRole.REVIEWER: {
        Permission.PROJECT_BANK_READ: _ASSIGNED,
        Permission.HUMAN_REVIEW_READ: _ASSIGNED,
        Permission.SCREEN: _ASSIGNED,
        Permission.EXTRACT: _ASSIGNED,
    },
    WorkspaceRole.VIEWER: {
        Permission.APPLICATION_READ: _FULL,
        Permission.SEARCH_HISTORY_READ: _FULL,
        Permission.EVIDENCE_LIBRARY_READ: _FULL,
        Permission.FULL_TEXT_ACCESS_READ: _FULL,
        Permission.PROJECT_BANK_READ: _FULL,
        Permission.HUMAN_REVIEW_READ: _FULL,
        Permission.EXPORT: _POLICY,
    },
    WorkspaceRole.GUEST_REVIEWER: {
        Permission.HUMAN_REVIEW_READ: _ASSIGNED,
        Permission.SCREEN: _ASSIGNED,
        Permission.EXTRACT: _ASSIGNED,
    },
}

_PROJECT_SCOPED = {
    Permission.APPLICATION_READ,
    Permission.APPLICATION_MANAGE,
    Permission.PROJECT_BANK_READ,
    Permission.HUMAN_REVIEW_READ,
    Permission.HUMAN_REVIEW_MANAGE,
    Permission.SCREEN,
    Permission.EXTRACT,
    Permission.ADJUDICATE,
    Permission.PROJECT_DELETE,
}

_OPTIONALLY_PROJECT_SCOPED = {
    Permission.SEARCH_RUN,
    Permission.SEARCH_HISTORY_READ,
    Permission.EXPORT,
    Permission.EVIDENCE_LIBRARY_READ,
    Permission.EVIDENCE_LIBRARY_WRITE,
    Permission.FULL_TEXT_ACCESS_READ,
    Permission.FULL_TEXT_ACCESS_MANAGE,
}


class PermissionService:
    """Fail-closed authorization contract for the multi-tenant platform.

    This service intentionally has no persistence or HTTP/session dependency. Callers must
    resolve the Principal and target project/workspace separately. Workspace/Project services
    establish ``project_access_confirmed`` before project-scoped permissions are evaluated.
    """

    def decide(
        self,
        principal: Principal,
        permission: Permission,
        *,
        context: AuthorizationContext | None = None,
    ) -> PermissionDecision:
        ctx = context or AuthorizationContext()

        if permission is Permission.PLATFORM_INFRA_MANAGE:
            if GlobalRole.PLATFORM_ADMIN in principal.global_roles:
                return PermissionDecision(
                    True,
                    permission,
                    PermissionScope.FULL,
                    GlobalRole.PLATFORM_ADMIN,
                    "global_role_grant",
                )
            return PermissionDecision(False, permission, reason="missing_platform_role")

        # PLATFORM_ADMIN is deliberately not a bypass for scientific/private workspace data.
        if ctx.workspace_id is None:
            return PermissionDecision(False, permission, reason="workspace_required")
        try:
            require_opaque_id(ctx.workspace_id, "workspace")
            if ctx.project_id is not None:
                require_opaque_id(ctx.project_id, "project")
        except ValueError:
            return PermissionDecision(False, permission, reason="invalid_target_id")

        membership = principal.membership_for(ctx.workspace_id)
        if membership is None:
            return PermissionDecision(False, permission, reason="active_membership_required")

        rule = ROLE_PERMISSIONS.get(membership.role, {}).get(permission)
        if rule is None:
            return PermissionDecision(
                False,
                permission,
                role=membership.role,
                reason="role_does_not_grant_permission",
            )

        project_access_required = permission in _PROJECT_SCOPED or (
            permission in _OPTIONALLY_PROJECT_SCOPED and ctx.project_id is not None
        )
        if project_access_required and not ctx.project_access_confirmed:
            return PermissionDecision(
                False,
                permission,
                role=membership.role,
                reason="project_access_not_confirmed",
            )

        if rule.policy_gated and permission not in ctx.policy_grants:
            return PermissionDecision(
                False,
                permission,
                role=membership.role,
                reason="explicit_policy_grant_required",
            )

        if rule.scope is PermissionScope.ASSIGNED and not ctx.assigned:
            return PermissionDecision(
                False,
                permission,
                role=membership.role,
                reason="assignment_required",
            )

        return PermissionDecision(
            True,
            permission,
            scope=rule.scope,
            role=membership.role,
            reason="role_grant",
        )

    def can(
        self,
        principal: Principal,
        permission: Permission,
        *,
        context: AuthorizationContext | None = None,
    ) -> bool:
        return self.decide(principal, permission, context=context).allowed

    def require(
        self,
        principal: Principal,
        permission: Permission,
        *,
        context: AuthorizationContext | None = None,
    ) -> PermissionDecision:
        decision = self.decide(principal, permission, context=context)
        if not decision.allowed:
            raise PermissionDenied(f"{permission.value}: {decision.reason}")
        return decision
