from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from typing import Iterable

from .models import (
    Membership,
    MembershipStatus,
    Principal,
    Project,
    Workspace,
    WorkspaceRole,
    new_opaque_id,
    require_opaque_id,
)
from .permissions import AuthorizationContext, Permission, PermissionService

TENANCY_SCHEMA_VERSION = 1
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_PROJECT_WIDE_ROLES = {
    WorkspaceRole.WORKSPACE_OWNER,
    WorkspaceRole.WORKSPACE_ADMIN,
    WorkspaceRole.RESEARCHER,
    WorkspaceRole.VIEWER,
}


class TenancyDataError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _slug(value: str) -> str:
    slug = str(value or "").strip().casefold()
    if not _SLUG_RE.fullmatch(slug):
        raise ValueError("slug must use lowercase letters, digits, and hyphens")
    return slug


def _apply_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS platform_tenancy_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS platform_workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            owner_user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active', 'suspended', 'deleted'))
        );
        CREATE INDEX IF NOT EXISTS idx_platform_workspaces_owner
            ON platform_workspaces(owner_user_id);

        CREATE TABLE IF NOT EXISTS platform_workspace_memberships (
            workspace_id TEXT NOT NULL REFERENCES platform_workspaces(id) ON DELETE CASCADE,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('invited', 'active', 'suspended', 'removed')),
            invited_by TEXT,
            joined_at TEXT,
            PRIMARY KEY(workspace_id, user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_platform_workspace_memberships_user
            ON platform_workspace_memberships(user_id, status);

        CREATE TABLE IF NOT EXISTS platform_projects (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL REFERENCES platform_workspaces(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            project_type TEXT NOT NULL DEFAULT 'generic',
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active', 'archived', 'deleted')),
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(workspace_id, slug)
        );
        CREATE INDEX IF NOT EXISTS idx_platform_projects_workspace
            ON platform_projects(workspace_id, status);

        CREATE TABLE IF NOT EXISTS platform_session_contexts (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            workspace_id TEXT,
            project_id TEXT,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_platform_session_contexts_user
            ON platform_session_contexts(user_id);
        """
    )
    connection.execute(
        "INSERT INTO platform_tenancy_meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(TENANCY_SCHEMA_VERSION),),
    )
    connection.commit()


@dataclass(frozen=True, slots=True)
class ResearchContext:
    workspace_id: str | None
    project_id: str | None


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    current: ResearchContext
    workspaces: tuple[Workspace, ...]
    projects: tuple[Project, ...]


class SQLiteWorkspaceProjectStore:
    """Platform tenancy store; contains ownership/access metadata, never scientific payloads."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path).resolve()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        _apply_schema(connection)
        return connection

    @staticmethod
    def _workspace(row: sqlite3.Row) -> Workspace:
        return Workspace(
            id=str(row["id"]),
            name=str(row["name"]),
            slug=str(row["slug"]),
            owner_user_id=str(row["owner_user_id"]),
            status=str(row["status"]),
            created_at=_parse_datetime(str(row["created_at"])) or _now(),
        )

    @staticmethod
    def _membership(row: sqlite3.Row) -> Membership:
        return Membership(
            workspace_id=str(row["workspace_id"]),
            user_id=str(row["user_id"]),
            role=WorkspaceRole(str(row["role"])),
            status=MembershipStatus(str(row["status"])),
            invited_by=str(row["invited_by"]) if row["invited_by"] else None,
            joined_at=_parse_datetime(str(row["joined_at"])) if row["joined_at"] else None,
        )

    @staticmethod
    def _project(row: sqlite3.Row) -> Project:
        return Project(
            id=str(row["id"]),
            workspace_id=str(row["workspace_id"]),
            name=str(row["name"]),
            slug=str(row["slug"]),
            description=str(row["description"]),
            project_type=str(row["project_type"]),
            status=str(row["status"]),
            created_by=str(row["created_by"]),
            created_at=_parse_datetime(str(row["created_at"])) or _now(),
            updated_at=_parse_datetime(str(row["updated_at"])) or _now(),
        )

    def create_workspace(
        self,
        *,
        owner_user_id: str,
        name: str,
        slug: str,
        workspace_id: str | None = None,
    ) -> Workspace:
        require_opaque_id(owner_user_id, "user")
        workspace_name = str(name or "").strip()
        if not workspace_name:
            raise ValueError("workspace name is required")
        canonical_slug = _slug(slug)
        wid = workspace_id or new_opaque_id("workspace")
        require_opaque_id(wid, "workspace")
        now = _now()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO platform_workspaces(id, name, slug, owner_user_id, created_at, status)
                    VALUES(?,?,?,?,?,'active')
                    """,
                    (wid, workspace_name, canonical_slug, owner_user_id, _iso(now)),
                )
                connection.execute(
                    """
                    INSERT INTO platform_workspace_memberships(
                        workspace_id, user_id, role, status, invited_by, joined_at
                    ) VALUES(?,?,?,'active',NULL,?)
                    """,
                    (wid, owner_user_id, WorkspaceRole.WORKSPACE_OWNER.value, _iso(now)),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("workspace id or slug already exists") from exc
        return Workspace(
            id=wid,
            name=workspace_name,
            slug=canonical_slug,
            owner_user_id=owner_user_id,
            created_at=now,
        )

    def memberships_for_user(self, user_id: str) -> tuple[Membership, ...]:
        try:
            require_opaque_id(user_id, "user")
        except ValueError:
            return ()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT workspace_id, user_id, role, status, invited_by, joined_at
                FROM platform_workspace_memberships
                WHERE user_id = ?
                ORDER BY workspace_id
                """,
                (user_id,),
            ).fetchall()
        return tuple(self._membership(row) for row in rows)

    def active_membership(self, user_id: str, workspace_id: str) -> Membership | None:
        try:
            require_opaque_id(user_id, "user")
            require_opaque_id(workspace_id, "workspace")
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT workspace_id, user_id, role, status, invited_by, joined_at
                FROM platform_workspace_memberships
                WHERE user_id = ? AND workspace_id = ? AND status = 'active'
                """,
                (user_id, workspace_id),
            ).fetchone()
        return self._membership(row) if row is not None else None

    def list_workspaces_for_user(self, user_id: str) -> tuple[Workspace, ...]:
        require_opaque_id(user_id, "user")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT w.*
                FROM platform_workspaces w
                JOIN platform_workspace_memberships m ON m.workspace_id = w.id
                WHERE m.user_id = ? AND m.status = 'active' AND w.status = 'active'
                ORDER BY w.name COLLATE NOCASE, w.id
                """,
                (user_id,),
            ).fetchall()
        return tuple(self._workspace(row) for row in rows)

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        try:
            require_opaque_id(workspace_id, "workspace")
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_workspaces WHERE id = ? AND status = 'active'",
                (workspace_id,),
            ).fetchone()
        return self._workspace(row) if row is not None else None

    def upsert_membership(
        self,
        *,
        workspace_id: str,
        user_id: str,
        role: WorkspaceRole,
        status: MembershipStatus = MembershipStatus.ACTIVE,
        invited_by: str | None = None,
    ) -> Membership:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(user_id, "user")
        if invited_by is not None:
            require_opaque_id(invited_by, "user")
        if self.get_workspace(workspace_id) is None:
            raise KeyError(workspace_id)
        joined_at = _now() if status is MembershipStatus.ACTIVE else None
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO platform_workspace_memberships(
                    workspace_id, user_id, role, status, invited_by, joined_at
                ) VALUES(?,?,?,?,?,?)
                ON CONFLICT(workspace_id, user_id) DO UPDATE SET
                    role=excluded.role,
                    status=excluded.status,
                    invited_by=excluded.invited_by,
                    joined_at=CASE
                        WHEN excluded.status='active' THEN COALESCE(platform_workspace_memberships.joined_at, excluded.joined_at)
                        ELSE platform_workspace_memberships.joined_at
                    END
                """,
                (
                    workspace_id,
                    user_id,
                    role.value,
                    status.value,
                    invited_by,
                    _iso(joined_at) if joined_at else None,
                ),
            )
            connection.commit()
            row = connection.execute(
                """
                SELECT workspace_id, user_id, role, status, invited_by, joined_at
                FROM platform_workspace_memberships
                WHERE workspace_id = ? AND user_id = ?
                """,
                (workspace_id, user_id),
            ).fetchone()
        if row is None:
            raise TenancyDataError("membership disappeared after upsert")
        return self._membership(row)

    def set_membership_status(
        self,
        *,
        workspace_id: str,
        user_id: str,
        status: MembershipStatus,
    ) -> None:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(user_id, "user")
        workspace = self.get_workspace(workspace_id)
        if workspace is None:
            raise KeyError(workspace_id)
        if workspace.owner_user_id == user_id and status is not MembershipStatus.ACTIVE:
            raise ValueError("workspace owner membership cannot be disabled")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE platform_workspace_memberships
                SET status = ?
                WHERE workspace_id = ? AND user_id = ?
                """,
                (status.value, workspace_id, user_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(user_id)
            connection.commit()

    def create_project(
        self,
        *,
        workspace_id: str,
        name: str,
        slug: str,
        created_by: str,
        description: str = "",
        project_type: str = "generic",
        project_id: str | None = None,
    ) -> Project:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(created_by, "user")
        project_name = str(name or "").strip()
        if not project_name:
            raise ValueError("project name is required")
        canonical_slug = _slug(slug)
        kind = str(project_type or "").strip()
        if not kind:
            raise ValueError("project_type is required")
        if self.get_workspace(workspace_id) is None:
            raise KeyError(workspace_id)
        pid = project_id or new_opaque_id("project")
        require_opaque_id(pid, "project")
        now = _now()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO platform_projects(
                        id, workspace_id, name, slug, description, project_type,
                        status, created_by, created_at, updated_at
                    ) VALUES(?,?,?,?,?,?,'active',?,?,?)
                    """,
                    (
                        pid,
                        workspace_id,
                        project_name,
                        canonical_slug,
                        str(description or ""),
                        kind,
                        created_by,
                        _iso(now),
                        _iso(now),
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("project id or slug already exists in workspace") from exc
        return Project(
            id=pid,
            workspace_id=workspace_id,
            name=project_name,
            slug=canonical_slug,
            description=str(description or ""),
            project_type=kind,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

    def get_project(self, project_id: str) -> Project | None:
        try:
            require_opaque_id(project_id, "project")
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_projects WHERE id = ? AND status = 'active'",
                (project_id,),
            ).fetchone()
        return self._project(row) if row is not None else None

    def list_projects(self, workspace_id: str) -> tuple[Project, ...]:
        require_opaque_id(workspace_id, "workspace")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM platform_projects
                WHERE workspace_id = ? AND status = 'active'
                ORDER BY name COLLATE NOCASE, id
                """,
                (workspace_id,),
            ).fetchall()
        return tuple(self._project(row) for row in rows)

    def save_context(
        self,
        *,
        session_id: str,
        user_id: str,
        workspace_id: str | None,
        project_id: str | None,
    ) -> None:
        require_opaque_id(session_id, "session")
        require_opaque_id(user_id, "user")
        if workspace_id is not None:
            require_opaque_id(workspace_id, "workspace")
        if project_id is not None:
            require_opaque_id(project_id, "project")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO platform_session_contexts(
                    session_id, user_id, workspace_id, project_id, updated_at
                ) VALUES(?,?,?,?,?)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_id=excluded.user_id,
                    workspace_id=excluded.workspace_id,
                    project_id=excluded.project_id,
                    updated_at=excluded.updated_at
                """,
                (session_id, user_id, workspace_id, project_id, _iso(_now())),
            )
            connection.commit()

    def load_context(self, *, session_id: str, user_id: str) -> ResearchContext:
        try:
            require_opaque_id(session_id, "session")
            require_opaque_id(user_id, "user")
        except ValueError:
            return ResearchContext(None, None)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT workspace_id, project_id
                FROM platform_session_contexts
                WHERE session_id = ? AND user_id = ?
                """,
                (session_id, user_id),
            ).fetchone()
        if row is None:
            return ResearchContext(None, None)
        return ResearchContext(
            workspace_id=str(row["workspace_id"]) if row["workspace_id"] else None,
            project_id=str(row["project_id"]) if row["project_id"] else None,
        )

    def clear_context(self, *, session_id: str, user_id: str) -> None:
        try:
            require_opaque_id(session_id, "session")
            require_opaque_id(user_id, "user")
        except ValueError:
            return
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM platform_session_contexts WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )
            connection.commit()


class WorkspaceProjectService:
    """Authoritative workspace/project access boundary for authenticated Principals."""

    def __init__(
        self,
        store: SQLiteWorkspaceProjectStore,
        *,
        permission_service: PermissionService | None = None,
    ) -> None:
        self.store = store
        self.permission_service = permission_service or PermissionService()

    def memberships_for_user(self, user_id: str) -> Iterable[Membership]:
        return self.store.memberships_for_user(user_id)

    def provision_workspace(
        self,
        *,
        owner_user_id: str,
        name: str,
        slug: str,
        workspace_id: str | None = None,
    ) -> Workspace:
        """Explicit bootstrap/migration primitive; intentionally not a public HTTP action in PR-3."""
        return self.store.create_workspace(
            owner_user_id=owner_user_id,
            name=name,
            slug=slug,
            workspace_id=workspace_id,
        )

    def list_workspaces(self, principal: Principal) -> tuple[Workspace, ...]:
        return self.store.list_workspaces_for_user(principal.user_id)

    def require_workspace(self, principal: Principal, workspace_id: str) -> Workspace:
        membership = principal.membership_for(workspace_id)
        if membership is None:
            raise PermissionError("workspace_access_denied")
        workspace = self.store.get_workspace(workspace_id)
        if workspace is None:
            raise KeyError(workspace_id)
        return workspace

    def add_or_update_member(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        user_id: str,
        role: WorkspaceRole,
        status: MembershipStatus = MembershipStatus.ACTIVE,
    ) -> Membership:
        self.permission_service.require(
            principal,
            Permission.MEMBERS_MANAGE,
            context=AuthorizationContext(workspace_id=workspace_id),
        )
        if role is WorkspaceRole.WORKSPACE_OWNER:
            raise ValueError("use explicit ownership transfer flow")
        return self.store.upsert_membership(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            status=status,
            invited_by=principal.user_id,
        )

    def set_member_status(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        user_id: str,
        status: MembershipStatus,
    ) -> None:
        self.permission_service.require(
            principal,
            Permission.MEMBERS_MANAGE,
            context=AuthorizationContext(workspace_id=workspace_id),
        )
        self.store.set_membership_status(
            workspace_id=workspace_id,
            user_id=user_id,
            status=status,
        )

    def create_project(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        name: str,
        slug: str,
        description: str = "",
        project_type: str = "generic",
        policy_grants: frozenset[Permission] = frozenset(),
        project_id: str | None = None,
    ) -> Project:
        self.require_workspace(principal, workspace_id)
        self.permission_service.require(
            principal,
            Permission.PROJECT_CREATE,
            context=AuthorizationContext(
                workspace_id=workspace_id,
                policy_grants=policy_grants,
            ),
        )
        return self.store.create_project(
            workspace_id=workspace_id,
            name=name,
            slug=slug,
            description=description,
            project_type=project_type,
            created_by=principal.user_id,
            project_id=project_id,
        )

    def _project_wide_access(self, principal: Principal, workspace_id: str) -> bool:
        membership = principal.membership_for(workspace_id)
        return membership is not None and membership.role in _PROJECT_WIDE_ROLES

    def confirm_project_access(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
    ) -> bool:
        try:
            self.require_workspace(principal, workspace_id)
        except (PermissionError, KeyError, ValueError):
            return False
        if not self._project_wide_access(principal, workspace_id):
            return False
        project = self.store.get_project(project_id)
        return project is not None and project.workspace_id == workspace_id

    def require_project(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
    ) -> Project:
        if not self.confirm_project_access(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        ):
            raise PermissionError("project_access_denied")
        project = self.store.get_project(project_id)
        if project is None:
            raise KeyError(project_id)
        return project

    def list_projects(self, principal: Principal, workspace_id: str) -> tuple[Project, ...]:
        self.require_workspace(principal, workspace_id)
        if not self._project_wide_access(principal, workspace_id):
            return ()
        return self.store.list_projects(workspace_id)

    def authorization_context(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str | None = None,
        assigned: bool = False,
        policy_grants: frozenset[Permission] = frozenset(),
    ) -> AuthorizationContext:
        self.require_workspace(principal, workspace_id)
        project_access = False
        if project_id is not None:
            project_access = self.confirm_project_access(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
            )
        return AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=project_access,
            assigned=assigned,
            policy_grants=policy_grants,
        )

    def select_context(
        self,
        principal: Principal,
        *,
        workspace_id: str | None,
        project_id: str | None = None,
    ) -> ContextSnapshot:
        if workspace_id is None:
            if project_id is not None:
                raise ValueError("project requires workspace")
            self.store.clear_context(
                session_id=principal.session_id,
                user_id=principal.user_id,
            )
            return self.context_snapshot(principal)

        self.require_workspace(principal, workspace_id)
        if project_id is not None:
            self.require_project(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
            )
        self.store.save_context(
            session_id=principal.session_id,
            user_id=principal.user_id,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        return self.context_snapshot(principal)

    def context_snapshot(self, principal: Principal) -> ContextSnapshot:
        workspaces = self.list_workspaces(principal)
        current = self.store.load_context(
            session_id=principal.session_id,
            user_id=principal.user_id,
        )
        workspace_ids = {workspace.id for workspace in workspaces}
        if current.workspace_id not in workspace_ids:
            if current.workspace_id is not None or current.project_id is not None:
                self.store.clear_context(
                    session_id=principal.session_id,
                    user_id=principal.user_id,
                )
            return ContextSnapshot(ResearchContext(None, None), workspaces, ())

        workspace_id = current.workspace_id
        if workspace_id is None:
            return ContextSnapshot(ResearchContext(None, None), workspaces, ())
        projects = self.list_projects(principal, workspace_id)
        project_ids = {project.id for project in projects}
        if current.project_id is not None and current.project_id not in project_ids:
            self.store.save_context(
                session_id=principal.session_id,
                user_id=principal.user_id,
                workspace_id=workspace_id,
                project_id=None,
            )
            current = ResearchContext(workspace_id, None)
        return ContextSnapshot(current, workspaces, projects)
