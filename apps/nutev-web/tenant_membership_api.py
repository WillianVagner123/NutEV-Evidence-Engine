"""Workspace member administration over HTTP.

The membership primitives already existed in ``WorkspaceProjectService`` but were reachable
only from an operator terminal. This module exposes them as a product surface for principals
holding ``MEMBERS_MANAGE`` (``WORKSPACE_OWNER`` / ``WORKSPACE_ADMIN``), without adding a second
identity, tenancy or permission implementation.

Boundaries this surface keeps:

- the target workspace comes from the authenticated server-side context, never from the body;
- ``WORKSPACE_OWNER`` is neither assignable nor removable here, so ownership never moves implicitly;
- granting membership never creates an identity; the person must already have an active account;
- changing an existing member's role requires an explicit acknowledgement, matching the CLI;
- membership is an access grant and never scientific approval, eligibility or PRISMA state.
"""
from __future__ import annotations

from http import HTTPStatus
import os
from pathlib import Path
import threading
from urllib.parse import urlparse

from nutev.tenancy import (
    ASSIGNABLE_WORKSPACE_ROLES,
    SQLiteAuthProvider,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
)
from nutev.tenancy.models import MembershipStatus, WorkspaceRole
from nutev.tenancy.permissions import (
    AuthorizationContext,
    Permission,
    PermissionDenied,
    PermissionService,
)
from server import APP_ROOT, NutEVHandler

_SERVICE_LOCK = threading.Lock()
_ACCESS: WorkspaceProjectService | None = None
_AUTH: SQLiteAuthProvider | None = None
_INSTALLED = False

# Statuses member administration may set. INVITED is not offered: this surface grants access to
# an account that already exists, so there is no pending-invitation state to represent here.
_ASSIGNABLE_STATUSES = {
    MembershipStatus.ACTIVE,
    MembershipStatus.SUSPENDED,
    MembershipStatus.REMOVED,
}


def _platform_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "auth.sqlite3").resolve()


def _access() -> WorkspaceProjectService:
    global _ACCESS
    with _SERVICE_LOCK:
        if _ACCESS is None:
            _ACCESS = WorkspaceProjectService(SQLiteWorkspaceProjectStore(_platform_database()))
        return _ACCESS


def _auth() -> SQLiteAuthProvider:
    global _AUTH
    with _SERVICE_LOCK:
        if _AUTH is None:
            _AUTH = SQLiteAuthProvider(_platform_database())
        return _AUTH


def _pilot_enabled(handler: NutEVHandler) -> bool:
    enabled = getattr(handler, "_auth_pilot_enabled", None)
    if not callable(enabled) or not enabled():
        handler._json({"error": "auth_pilot_disabled"}, HTTPStatus.NOT_FOUND)
        return False
    return True


def _workspace_context(handler: NutEVHandler):
    """Resolve the Principal and the server-side selected workspace.

    The workspace is taken from the authenticated session context only. A ``workspace_id`` in
    the request body is never read, so knowing a foreign ID cannot target another tenant.
    """
    if not _pilot_enabled(handler):
        return None
    resolver = getattr(handler, "_tenant_search_session", None)
    if not callable(resolver):
        handler._json({"error": "authentication_required"}, HTTPStatus.UNAUTHORIZED)
        return None
    resolved = resolver()
    if resolved is None:
        return None
    session, snapshot = resolved
    workspace_id = snapshot.current.workspace_id
    if not workspace_id:
        handler._json({"error": "workspace_context_required"}, HTTPStatus.CONFLICT)
        return None
    return session.principal, workspace_id


def _can_manage(principal, workspace_id: str) -> bool:
    return PermissionService().can(
        principal,
        Permission.MEMBERS_MANAGE,
        context=AuthorizationContext(workspace_id=workspace_id),
    )


def _member_payload(membership, *, subject, workspace, current_user_id: str) -> dict[str, object]:
    return {
        "user_id": membership.user_id,
        "display_name": subject.user.display_name if subject is not None else "",
        "email": subject.user.email if subject is not None else "",
        "role": membership.role.value,
        "status": membership.status.value,
        "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
        "is_workspace_owner": membership.user_id == workspace.owner_user_id,
        "is_current_user": membership.user_id == current_user_id,
        # Ownership never moves through member administration, and the sitting owner's role is
        # not editable here, so the UI can render those controls as unavailable rather than
        # offering an action the server will refuse.
        "role_editable": membership.user_id != workspace.owner_user_id,
        "status_editable": membership.user_id != workspace.owner_user_id,
    }


def _list_members(handler: NutEVHandler) -> bool:
    resolved = _workspace_context(handler)
    if resolved is None:
        return True
    principal, workspace_id = resolved
    try:
        memberships = _access().list_members(principal, workspace_id)
        workspace = _access().store.get_workspace(workspace_id)
    except PermissionDenied:
        handler._json({"error": "members_manage_required"}, HTTPStatus.FORBIDDEN)
        return True
    except (KeyError, ValueError):
        handler._json({"error": "workspace_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    except Exception:
        handler._json({"error": "membership_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True
    if workspace is None:
        handler._json({"error": "workspace_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    provider = _auth()
    members = [
        _member_payload(
            membership,
            subject=provider.load_subject(membership.user_id),
            workspace=workspace,
            current_user_id=principal.user_id,
        )
        for membership in memberships
    ]
    handler._json(
        {
            "workspace": {"id": workspace.id, "name": workspace.name, "slug": workspace.slug},
            "members": members,
            "assignable_roles": [role.value for role in ASSIGNABLE_WORKSPACE_ROLES],
            "assignable_statuses": sorted(status.value for status in _ASSIGNABLE_STATUSES),
            "owner_role_assignable": False,
            "membership_creates_identity": False,
            "membership_is_scientific_approval": False,
        }
    )
    return True


def _grant_member(handler: NutEVHandler) -> bool:
    resolved = _workspace_context(handler)
    if resolved is None:
        return True
    principal, workspace_id = resolved
    if not _can_manage(principal, workspace_id):
        handler._json({"error": "members_manage_required"}, HTTPStatus.FORBIDDEN)
        return True
    try:
        payload = handler._read_json()
    except ValueError:
        handler._json({"error": "invalid_membership_request"}, HTTPStatus.BAD_REQUEST)
        return True
    try:
        role = WorkspaceRole(str(payload.get("role") or "").strip())
    except ValueError:
        handler._json({"error": "invalid_membership_role"}, HTTPStatus.BAD_REQUEST)
        return True
    if role not in ASSIGNABLE_WORKSPACE_ROLES:
        handler._json({"error": "role_not_assignable"}, HTTPStatus.BAD_REQUEST)
        return True

    subject = _auth().find_active_subject_by_email(str(payload.get("email") or ""))
    if subject is None:
        # The person must already have completed the governed invitation flow. Refusing here
        # keeps member administration from becoming a second account-provisioning path.
        handler._json({"error": "active_account_not_found"}, HTTPStatus.NOT_FOUND)
        return True

    store = _access().store
    existing = next(
        (row for row in store.list_memberships(workspace_id) if row.user_id == subject.user.id),
        None,
    )
    changes_role = existing is not None and existing.role is not role
    if changes_role and not bool(payload.get("allow_role_change")):
        handler._json(
            {
                "error": "role_change_requires_explicit_confirmation",
                "current_role": existing.role.value,
                "requested_role": role.value,
            },
            HTTPStatus.CONFLICT,
        )
        return True

    try:
        membership = _access().add_or_update_member(
            principal,
            workspace_id=workspace_id,
            user_id=subject.user.id,
            role=role,
            status=MembershipStatus.ACTIVE,
        )
    except PermissionDenied:
        handler._json({"error": "members_manage_required"}, HTTPStatus.FORBIDDEN)
        return True
    except KeyError:
        handler._json({"error": "workspace_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    except ValueError:
        # Covers both assigning WORKSPACE_OWNER and demoting the sitting owner.
        handler._json({"error": "ownership_transfer_not_supported_here"}, HTTPStatus.CONFLICT)
        return True
    except Exception:
        handler._json({"error": "membership_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True

    handler._json(
        {
            "status": "role_changed" if changes_role else ("already_granted" if existing else "membership_granted"),
            "changed": existing is None or existing.role is not role or not existing.active,
            "member": {
                "user_id": membership.user_id,
                "display_name": subject.user.display_name,
                "email": subject.user.email,
                "role": membership.role.value,
                "status": membership.status.value,
            },
            "user_created": False,
            "global_role_granted": False,
            "scientific_state_modified": False,
            "scientific_approval_created": False,
        }
    )
    return True


def _set_member_status(handler: NutEVHandler) -> bool:
    resolved = _workspace_context(handler)
    if resolved is None:
        return True
    principal, workspace_id = resolved
    if not _can_manage(principal, workspace_id):
        handler._json({"error": "members_manage_required"}, HTTPStatus.FORBIDDEN)
        return True
    try:
        payload = handler._read_json()
    except ValueError:
        handler._json({"error": "invalid_membership_request"}, HTTPStatus.BAD_REQUEST)
        return True
    try:
        status = MembershipStatus(str(payload.get("status") or "").strip())
    except ValueError:
        handler._json({"error": "invalid_membership_status"}, HTTPStatus.BAD_REQUEST)
        return True
    if status not in _ASSIGNABLE_STATUSES:
        handler._json({"error": "status_not_assignable"}, HTTPStatus.BAD_REQUEST)
        return True
    user_id = str(payload.get("user_id") or "").strip()

    try:
        _access().set_member_status(
            principal,
            workspace_id=workspace_id,
            user_id=user_id,
            status=status,
        )
    except PermissionDenied:
        handler._json({"error": "members_manage_required"}, HTTPStatus.FORBIDDEN)
        return True
    except KeyError:
        handler._json({"error": "membership_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    except ValueError:
        # Raised for a malformed id and for disabling the workspace owner's membership.
        handler._json({"error": "membership_status_refused"}, HTTPStatus.CONFLICT)
        return True
    except Exception:
        handler._json({"error": "membership_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True

    handler._json(
        {
            "status": "membership_status_updated",
            "changed": True,
            "member": {"user_id": user_id, "status": status.value},
            "scientific_state_modified": False,
            "scientific_approval_created": False,
        }
    )
    return True


def _membership_get(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/workspace/members":
        return _list_members(handler)
    return False


def _membership_post(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/workspace/members":
        return _grant_member(handler)
    if parsed.path == "/api/workspace/members/status":
        return _set_member_status(handler)
    return False


def install_membership_routes() -> None:
    """Install workspace member administration without touching scientific state."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    original_get = NutEVHandler.do_GET
    original_post = NutEVHandler.do_POST

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _membership_get(self, parsed):
            return
        original_get(self)

    def do_post(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _membership_post(self, parsed):
            return
        original_post(self)

    NutEVHandler.do_GET = do_get
    NutEVHandler.do_POST = do_post
