from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import re
from uuid import uuid4

_ID_RE = re.compile(r"^(?P<prefix>[a-z]{3})_[a-f0-9]{32}$")
_PREFIX_BY_KIND = {
    "user": "usr",
    "workspace": "wsp",
    "project": "prj",
    "application": "app",
    "session": "ses",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_opaque_id(kind: str) -> str:
    try:
        prefix = _PREFIX_BY_KIND[kind]
    except KeyError as exc:
        raise ValueError(f"unsupported opaque id kind: {kind}") from exc
    return f"{prefix}_{uuid4().hex}"


def require_opaque_id(value: str, kind: str) -> str:
    expected = _PREFIX_BY_KIND.get(kind)
    match = _ID_RE.fullmatch(str(value or ""))
    if expected is None or match is None or match.group("prefix") != expected:
        raise ValueError(f"invalid {kind}_id")
    return value


class GlobalRole(StrEnum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class WorkspaceRole(StrEnum):
    WORKSPACE_OWNER = "WORKSPACE_OWNER"
    WORKSPACE_ADMIN = "WORKSPACE_ADMIN"
    RESEARCHER = "RESEARCHER"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"
    GUEST_REVIEWER = "GUEST_REVIEWER"


class MembershipStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class User:
    id: str
    email: str
    display_name: str
    status: str = "active"
    created_at: datetime = field(default_factory=utcnow)
    last_login_at: datetime | None = None

    def __post_init__(self) -> None:
        require_opaque_id(self.id, "user")
        if not self.email.strip() or "@" not in self.email:
            raise ValueError("email is required")
        if not self.display_name.strip():
            raise ValueError("display_name is required")


@dataclass(frozen=True, slots=True)
class Workspace:
    id: str
    name: str
    slug: str
    owner_user_id: str
    status: str = "active"
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        require_opaque_id(self.id, "workspace")
        require_opaque_id(self.owner_user_id, "user")
        if not self.name.strip():
            raise ValueError("workspace name is required")
        if not self.slug.strip():
            raise ValueError("workspace slug is required")


@dataclass(frozen=True, slots=True)
class Membership:
    workspace_id: str
    user_id: str
    role: WorkspaceRole
    status: MembershipStatus = MembershipStatus.ACTIVE
    invited_by: str | None = None
    joined_at: datetime | None = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        require_opaque_id(self.workspace_id, "workspace")
        require_opaque_id(self.user_id, "user")
        if self.invited_by is not None:
            require_opaque_id(self.invited_by, "user")

    @property
    def active(self) -> bool:
        return self.status is MembershipStatus.ACTIVE


WorkspaceMembership = Membership


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    workspace_id: str
    name: str
    slug: str
    created_by: str
    description: str = ""
    project_type: str = "generic"
    status: str = "active"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        require_opaque_id(self.id, "project")
        require_opaque_id(self.workspace_id, "workspace")
        require_opaque_id(self.created_by, "user")
        if not self.name.strip():
            raise ValueError("project name is required")
        if not self.slug.strip():
            raise ValueError("project slug is required")
        if not self.project_type.strip():
            raise ValueError("project_type is required")


@dataclass(frozen=True, slots=True)
class ResearchApplication:
    id: str
    project_id: str
    application_type: str
    template_id: str | None = None
    config_version: str = "1"
    status: str = "active"
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        require_opaque_id(self.id, "application")
        require_opaque_id(self.project_id, "project")
        if not self.application_type.strip():
            raise ValueError("application_type is required")
        if not self.config_version.strip():
            raise ValueError("config_version is required")


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    workspace_memberships: tuple[Membership, ...]
    global_roles: frozenset[GlobalRole]
    session_id: str

    def __post_init__(self) -> None:
        require_opaque_id(self.user_id, "user")
        require_opaque_id(self.session_id, "session")
        seen: set[str] = set()
        for membership in self.workspace_memberships:
            if membership.user_id != self.user_id:
                raise ValueError("principal membership belongs to another user")
            if membership.workspace_id in seen:
                raise ValueError("principal has duplicate workspace membership")
            seen.add(membership.workspace_id)

    def membership_for(self, workspace_id: str) -> Membership | None:
        require_opaque_id(workspace_id, "workspace")
        for membership in self.workspace_memberships:
            if membership.workspace_id == workspace_id and membership.active:
                return membership
        return None
