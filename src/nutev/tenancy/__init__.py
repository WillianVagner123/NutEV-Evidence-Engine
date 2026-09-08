"""Identity and authorization contracts for NutEV multi-tenant boundaries."""

from .models import (
    GlobalRole,
    Membership,
    MembershipStatus,
    Principal,
    Project,
    ResearchApplication,
    User,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
    new_opaque_id,
    require_opaque_id,
)
from .permissions import (
    AuthorizationContext,
    Permission,
    PermissionDecision,
    PermissionDenied,
    PermissionRule,
    PermissionScope,
    PermissionService,
    ROLE_PERMISSIONS,
)

__all__ = [
    "AuthorizationContext",
    "GlobalRole",
    "Membership",
    "MembershipStatus",
    "Permission",
    "PermissionDecision",
    "PermissionDenied",
    "PermissionRule",
    "PermissionScope",
    "PermissionService",
    "Principal",
    "Project",
    "ROLE_PERMISSIONS",
    "ResearchApplication",
    "User",
    "Workspace",
    "WorkspaceMembership",
    "WorkspaceRole",
    "new_opaque_id",
    "require_opaque_id",
]
