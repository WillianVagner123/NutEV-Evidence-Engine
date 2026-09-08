from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3

from .models import Principal, require_opaque_id
from .permissions import AuthorizationContext, Permission, PermissionService
from .access import ResearchContext, WorkspaceProjectService

SEARCH_OWNERSHIP_SCHEMA_VERSION = 1
_JOB_RE = re.compile(r"^job_[a-f0-9]{32}$")
_SEARCH_RE = re.compile(r"^web_[A-Za-z0-9+_-]+$")


class SearchOwnershipError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _validate_job_id(value: str) -> str:
    job_id = str(value or "").strip()
    if not _JOB_RE.fullmatch(job_id):
        raise ValueError("invalid job_id")
    return job_id


def _validate_search_id(value: str) -> str:
    search_id = str(value or "").strip()
    if not _SEARCH_RE.fullmatch(search_id):
        raise ValueError("invalid search_id")
    return search_id


def _apply_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS platform_search_scope_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS platform_search_ownership (
            job_id TEXT PRIMARY KEY,
            search_id TEXT UNIQUE,
            workspace_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            project_id TEXT,
            created_at TEXT NOT NULL,
            search_bound_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_platform_search_owner_workspace
            ON platform_search_ownership(workspace_id, search_bound_at);
        CREATE INDEX IF NOT EXISTS idx_platform_search_owner_project
            ON platform_search_ownership(workspace_id, project_id, search_bound_at);
        CREATE INDEX IF NOT EXISTS idx_platform_search_owner_user
            ON platform_search_ownership(user_id, search_bound_at);
        """
    )
    connection.execute(
        "INSERT INTO platform_search_scope_meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(SEARCH_OWNERSHIP_SCHEMA_VERSION),),
    )
    connection.commit()


@dataclass(frozen=True, slots=True)
class SearchOwnership:
    job_id: str
    search_id: str | None
    workspace_id: str
    user_id: str
    project_id: str | None
    created_at: datetime
    search_bound_at: datetime | None


class SQLiteSearchOwnershipStore:
    """Private ownership metadata for new authenticated search jobs/runs.

    Historical runs are intentionally absent until the explicit migration PR. Absence from
    this table therefore means "not adopted into authenticated tenancy", never "global".
    """

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
    def _ownership(row: sqlite3.Row) -> SearchOwnership:
        return SearchOwnership(
            job_id=str(row["job_id"]),
            search_id=str(row["search_id"]) if row["search_id"] else None,
            workspace_id=str(row["workspace_id"]),
            user_id=str(row["user_id"]),
            project_id=str(row["project_id"]) if row["project_id"] else None,
            created_at=datetime.fromisoformat(str(row["created_at"])),
            search_bound_at=(
                datetime.fromisoformat(str(row["search_bound_at"]))
                if row["search_bound_at"]
                else None
            ),
        )

    def record_job(
        self,
        *,
        job_id: str,
        workspace_id: str,
        user_id: str,
        project_id: str | None,
    ) -> SearchOwnership:
        jid = _validate_job_id(job_id)
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(user_id, "user")
        if project_id is not None:
            require_opaque_id(project_id, "project")
        created_at = _now()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO platform_search_ownership(
                        job_id, search_id, workspace_id, user_id, project_id,
                        created_at, search_bound_at
                    ) VALUES(?,NULL,?,?,?,?,NULL)
                    """,
                    (jid, workspace_id, user_id, project_id, _iso(created_at)),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise SearchOwnershipError("job ownership already exists") from exc
        owner = self.owner_for_job(jid)
        if owner is None:
            raise SearchOwnershipError("job ownership disappeared after insert")
        return owner

    def bind_search(self, *, job_id: str, search_id: str) -> SearchOwnership:
        jid = _validate_job_id(job_id)
        sid = _validate_search_id(search_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT search_id FROM platform_search_ownership WHERE job_id = ?",
                (jid,),
            ).fetchone()
            if row is None:
                raise SearchOwnershipError("job ownership is missing")
            existing = str(row["search_id"]) if row["search_id"] else None
            if existing is not None and existing != sid:
                raise SearchOwnershipError("job already bound to another search")
            try:
                connection.execute(
                    """
                    UPDATE platform_search_ownership
                    SET search_id = ?, search_bound_at = COALESCE(search_bound_at, ?)
                    WHERE job_id = ?
                    """,
                    (sid, _iso(_now()), jid),
                )
                connection.commit()
            except sqlite3.IntegrityError as exc:
                raise SearchOwnershipError("search ownership conflict") from exc
        owner = self.owner_for_job(jid)
        if owner is None:
            raise SearchOwnershipError("search ownership disappeared after bind")
        return owner

    def owner_for_job(self, job_id: str) -> SearchOwnership | None:
        try:
            jid = _validate_job_id(job_id)
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_search_ownership WHERE job_id = ?",
                (jid,),
            ).fetchone()
        return self._ownership(row) if row is not None else None

    def owner_for_search(self, search_id: str) -> SearchOwnership | None:
        try:
            sid = _validate_search_id(search_id)
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_search_ownership WHERE search_id = ?",
                (sid,),
            ).fetchone()
        return self._ownership(row) if row is not None else None

    def search_ids_for_workspace(self, workspace_id: str) -> frozenset[str]:
        require_opaque_id(workspace_id, "workspace")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT search_id FROM platform_search_ownership
                WHERE workspace_id = ? AND search_id IS NOT NULL
                ORDER BY search_bound_at DESC, job_id DESC
                """,
                (workspace_id,),
            ).fetchall()
        return frozenset(str(row["search_id"]) for row in rows if row["search_id"])

    def search_ids_for_project(self, workspace_id: str, project_id: str) -> frozenset[str]:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT search_id FROM platform_search_ownership
                WHERE workspace_id = ? AND project_id = ? AND search_id IS NOT NULL
                ORDER BY search_bound_at DESC, job_id DESC
                """,
                (workspace_id, project_id),
            ).fetchall()
        return frozenset(str(row["search_id"]) for row in rows if row["search_id"])


class SearchScopeService:
    """Authorization facade for tenant-scoped search jobs and history."""

    def __init__(
        self,
        store: SQLiteSearchOwnershipStore,
        workspace_service: WorkspaceProjectService,
        *,
        permission_service: PermissionService | None = None,
    ) -> None:
        self.store = store
        self.workspace_service = workspace_service
        self.permission_service = permission_service or PermissionService()

    def authorize_new_search(
        self,
        principal: Principal,
        context: ResearchContext,
    ) -> AuthorizationContext:
        if context.workspace_id is None:
            raise PermissionError("workspace_context_required")
        auth_context = self.workspace_service.authorization_context(
            principal,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
        )
        self.permission_service.require(
            principal,
            Permission.SEARCH_RUN,
            context=auth_context,
        )
        return auth_context

    def record_new_job(
        self,
        principal: Principal,
        context: ResearchContext,
        *,
        job_id: str,
    ) -> SearchOwnership:
        self.authorize_new_search(principal, context)
        assert context.workspace_id is not None
        return self.store.record_job(
            job_id=job_id,
            workspace_id=context.workspace_id,
            user_id=principal.user_id,
            project_id=context.project_id,
        )

    def _history_context(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str | None,
    ) -> AuthorizationContext:
        auth_context = self.workspace_service.authorization_context(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        self.permission_service.require(
            principal,
            Permission.SEARCH_HISTORY_READ,
            context=auth_context,
        )
        return auth_context

    def require_job_access(
        self,
        principal: Principal,
        current: ResearchContext,
        job_id: str,
    ) -> SearchOwnership:
        owner = self.store.owner_for_job(job_id)
        if owner is None or current.workspace_id != owner.workspace_id:
            raise PermissionError("search_job_not_found")
        self._history_context(
            principal,
            workspace_id=owner.workspace_id,
            project_id=owner.project_id,
        )
        return owner

    def require_search_access(
        self,
        principal: Principal,
        current: ResearchContext,
        search_id: str,
    ) -> SearchOwnership:
        owner = self.store.owner_for_search(search_id)
        if owner is None or current.workspace_id != owner.workspace_id:
            raise PermissionError("search_not_found")
        self._history_context(
            principal,
            workspace_id=owner.workspace_id,
            project_id=owner.project_id,
        )
        return owner

    def authorized_search_ids(
        self,
        principal: Principal,
        current: ResearchContext,
        *,
        scope: str,
    ) -> frozenset[str]:
        if current.workspace_id is None:
            raise PermissionError("workspace_context_required")
        normalized = str(scope or "workspace").strip().casefold()
        if normalized == "project":
            if current.project_id is None:
                raise PermissionError("project_context_required")
            self._history_context(
                principal,
                workspace_id=current.workspace_id,
                project_id=current.project_id,
            )
            return self.store.search_ids_for_project(current.workspace_id, current.project_id)
        if normalized != "workspace":
            raise ValueError("invalid search history scope")
        self._history_context(
            principal,
            workspace_id=current.workspace_id,
            project_id=None,
        )
        return self.store.search_ids_for_workspace(current.workspace_id)
