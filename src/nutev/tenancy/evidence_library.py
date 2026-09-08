from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
from typing import Any
from uuid import uuid4

from .access import ResearchContext, WorkspaceProjectService
from .models import Principal, require_opaque_id
from .permissions import AuthorizationContext, Permission, PermissionService

EVIDENCE_LIBRARY_SCHEMA_VERSION = 1
_PLACEMENT_RE = re.compile(r"^plc_[a-f0-9]{32}$")
_GRANT_RE = re.compile(r"^ftg_[a-f0-9]{32}$")
_ALLOWED_STATES = {"not_screened", "included", "excluded", "background"}


class EvidenceLibraryError(RuntimeError):
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


def _placement_id() -> str:
    return "plc_" + uuid4().hex


def _grant_id() -> str:
    return "ftg_" + uuid4().hex


def _validate_placement_id(value: str) -> str:
    placement_id = str(value or "").strip()
    if not _PLACEMENT_RE.fullmatch(placement_id):
        raise ValueError("invalid placement_id")
    return placement_id


def _validate_grant_id(value: str) -> str:
    grant_id = str(value or "").strip()
    if not _GRANT_RE.fullmatch(grant_id):
        raise ValueError("invalid grant_id")
    return grant_id


def _state(value: str) -> str:
    state = str(value or "not_screened").strip().casefold()
    if state not in _ALLOWED_STATES:
        raise ValueError("invalid placement state")
    return state


def _tags(values: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    output: list[str] = []
    seen: set[str] = set()
    for raw in values or ():
        value = " ".join(str(raw or "").split())[:80]
        if not value:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
        if len(output) >= 30:
            break
    return tuple(output)


def _note(value: str) -> str:
    return str(value or "").strip()[:8000]


def _apply_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS platform_evidence_library_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS platform_document_placements (
            placement_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            project_id TEXT,
            article_id TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'not_screened'
                CHECK(state IN ('not_screened', 'included', 'excluded', 'background')),
            tags_json TEXT NOT NULL DEFAULT '[]',
            notes TEXT NOT NULL DEFAULT '',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_placement_unique_scope
            ON platform_document_placements(workspace_id, COALESCE(project_id, ''), article_id);
        CREATE INDEX IF NOT EXISTS idx_platform_placement_workspace
            ON platform_document_placements(workspace_id, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_platform_placement_project
            ON platform_document_placements(workspace_id, project_id, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_platform_placement_article
            ON platform_document_placements(article_id);

        CREATE TABLE IF NOT EXISTS platform_full_text_access_grants (
            grant_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            project_id TEXT,
            article_id TEXT NOT NULL,
            artifact_id TEXT,
            provider_record_id TEXT NOT NULL DEFAULT '',
            access_type TEXT NOT NULL,
            license_text TEXT NOT NULL DEFAULT '',
            access_url TEXT NOT NULL DEFAULT '',
            cache_path TEXT NOT NULL DEFAULT '',
            redistribution_allowed INTEGER NOT NULL DEFAULT 0
                CHECK(redistribution_allowed IN (0, 1)),
            expires_at TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_platform_fulltext_grant_scope
            ON platform_full_text_access_grants(workspace_id, project_id, article_id);
        CREATE INDEX IF NOT EXISTS idx_platform_fulltext_grant_article
            ON platform_full_text_access_grants(article_id);
        """
    )
    connection.execute(
        "INSERT INTO platform_evidence_library_meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(EVIDENCE_LIBRARY_SCHEMA_VERSION),),
    )
    connection.commit()


@dataclass(frozen=True, slots=True)
class GlobalDocument:
    article_id: str
    title: str
    year: int | None
    journal: str
    abstract: str
    doi: str | None
    pmid: str | None
    pmcid: str | None


@dataclass(frozen=True, slots=True)
class Placement:
    placement_id: str
    workspace_id: str
    project_id: str | None
    article_id: str
    state: str
    tags: tuple[str, ...]
    notes: str
    created_by: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class EvidenceLibraryEntry:
    placement: Placement
    document: GlobalDocument


@dataclass(frozen=True, slots=True)
class FullTextAccessGrant:
    grant_id: str
    workspace_id: str
    project_id: str | None
    article_id: str
    artifact_id: str | None
    provider_record_id: str
    access_type: str
    license_text: str
    access_url: str
    cache_path: str
    redistribution_allowed: bool
    expires_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    @property
    def active(self) -> bool:
        return self.expires_at is None or self.expires_at > _now()

    def public_descriptor(self) -> dict[str, Any]:
        """Safe descriptor: cache/storage paths are never exposed to browser clients."""
        return {
            "grant_id": self.grant_id,
            "article_id": self.article_id,
            "artifact_id": self.artifact_id,
            "provider_record_id": self.provider_record_id,
            "access_type": self.access_type,
            "license": self.license_text,
            "access_url": self.access_url,
            "redistribution_allowed": self.redistribution_allowed,
            "expires_at": _iso(self.expires_at) if self.expires_at else None,
        }


class GlobalEvidenceRegistryReader:
    """Read-only global bibliographic view over the canonical Article Registry."""

    def __init__(self, registry_database: Path) -> None:
        self.registry_database = Path(registry_database).resolve()

    def _connect(self) -> sqlite3.Connection:
        if not self.registry_database.is_file():
            raise FileNotFoundError(self.registry_database)
        connection = sqlite3.connect(
            f"file:{self.registry_database}?mode=ro",
            uri=True,
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        return connection

    def get(self, article_id: str) -> GlobalDocument | None:
        article_id = str(article_id or "").strip()
        if not article_id:
            return None
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT article_id, canonical_title, publication_year, journal, abstract
                FROM articles
                WHERE article_id = ? AND registry_status = 'active'
                """,
                (article_id,),
            ).fetchone()
            if row is None:
                return None
            aliases = connection.execute(
                """
                SELECT scheme, normalized_value
                FROM article_aliases
                WHERE article_id = ? AND scheme IN ('doi', 'pmid', 'pmcid')
                ORDER BY alias_id
                """,
                (article_id,),
            ).fetchall()
        by_scheme: dict[str, str] = {}
        for alias in aliases:
            by_scheme.setdefault(str(alias["scheme"]), str(alias["normalized_value"]))
        return GlobalDocument(
            article_id=str(row["article_id"]),
            title=str(row["canonical_title"] or ""),
            year=int(row["publication_year"]) if row["publication_year"] is not None else None,
            journal=str(row["journal"] or ""),
            abstract=str(row["abstract"] or ""),
            doi=by_scheme.get("doi"),
            pmid=by_scheme.get("pmid"),
            pmcid=by_scheme.get("pmcid"),
        )

    def get_many(self, article_ids: list[str] | tuple[str, ...]) -> dict[str, GlobalDocument]:
        unique = [value for value in dict.fromkeys(str(item or "").strip() for item in article_ids) if value]
        return {article_id: document for article_id in unique if (document := self.get(article_id)) is not None}


class SQLiteEvidenceLibraryStore:
    """Private placement/grant store. It never contains canonical article metadata."""

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
    def _placement(row: sqlite3.Row) -> Placement:
        try:
            raw_tags = json.loads(str(row["tags_json"] or "[]"))
        except json.JSONDecodeError as exc:
            raise EvidenceLibraryError("invalid placement tags payload") from exc
        if not isinstance(raw_tags, list):
            raise EvidenceLibraryError("invalid placement tags payload")
        return Placement(
            placement_id=str(row["placement_id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]) if row["project_id"] else None,
            article_id=str(row["article_id"]),
            state=str(row["state"]),
            tags=tuple(str(item) for item in raw_tags),
            notes=str(row["notes"] or ""),
            created_by=str(row["created_by"]),
            created_at=_parse_datetime(str(row["created_at"])) or _now(),
            updated_at=_parse_datetime(str(row["updated_at"])) or _now(),
        )

    @staticmethod
    def _grant(row: sqlite3.Row) -> FullTextAccessGrant:
        return FullTextAccessGrant(
            grant_id=str(row["grant_id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]) if row["project_id"] else None,
            article_id=str(row["article_id"]),
            artifact_id=str(row["artifact_id"]) if row["artifact_id"] else None,
            provider_record_id=str(row["provider_record_id"] or ""),
            access_type=str(row["access_type"]),
            license_text=str(row["license_text"] or ""),
            access_url=str(row["access_url"] or ""),
            cache_path=str(row["cache_path"] or ""),
            redistribution_allowed=bool(row["redistribution_allowed"]),
            expires_at=_parse_datetime(str(row["expires_at"])) if row["expires_at"] else None,
            created_by=str(row["created_by"]),
            created_at=_parse_datetime(str(row["created_at"])) or _now(),
            updated_at=_parse_datetime(str(row["updated_at"])) or _now(),
        )

    def upsert_placement(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        article_id: str,
        state: str,
        tags: tuple[str, ...],
        notes: str,
        created_by: str,
    ) -> Placement:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(created_by, "user")
        if project_id is not None:
            require_opaque_id(project_id, "project")
        canonical_state = _state(state)
        now = _now()
        encoded_tags = json.dumps(list(tags), ensure_ascii=False, separators=(",", ":"))
        placement_id = _placement_id()
        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT placement_id FROM platform_document_placements
                WHERE workspace_id = ? AND COALESCE(project_id, '') = COALESCE(?, '')
                  AND article_id = ?
                """,
                (workspace_id, project_id, article_id),
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO platform_document_placements(
                        placement_id, workspace_id, project_id, article_id, state,
                        tags_json, notes, created_by, created_at, updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        placement_id,
                        workspace_id,
                        project_id,
                        article_id,
                        canonical_state,
                        encoded_tags,
                        notes,
                        created_by,
                        _iso(now),
                        _iso(now),
                    ),
                )
            else:
                placement_id = str(existing["placement_id"])
                connection.execute(
                    """
                    UPDATE platform_document_placements
                    SET state = ?, tags_json = ?, notes = ?, updated_at = ?
                    WHERE placement_id = ?
                    """,
                    (canonical_state, encoded_tags, notes, _iso(now), placement_id),
                )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM platform_document_placements WHERE placement_id = ?",
                (placement_id,),
            ).fetchone()
        if row is None:
            raise EvidenceLibraryError("placement disappeared after upsert")
        return self._placement(row)

    def get_placement(self, placement_id: str) -> Placement | None:
        try:
            placement_id = _validate_placement_id(placement_id)
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_document_placements WHERE placement_id = ?",
                (placement_id,),
            ).fetchone()
        return self._placement(row) if row is not None else None

    def find_placement(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        article_id: str,
    ) -> Placement | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM platform_document_placements
                WHERE workspace_id = ? AND COALESCE(project_id, '') = COALESCE(?, '')
                  AND article_id = ?
                """,
                (workspace_id, project_id, article_id),
            ).fetchone()
        return self._placement(row) if row is not None else None

    def list_placements(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        project_only: bool,
        limit: int = 200,
    ) -> tuple[Placement, ...]:
        with self._connect() as connection:
            if project_only:
                rows = connection.execute(
                    """
                    SELECT * FROM platform_document_placements
                    WHERE workspace_id = ? AND project_id = ?
                    ORDER BY updated_at DESC, placement_id
                    LIMIT ?
                    """,
                    (workspace_id, project_id, max(1, min(int(limit), 500))),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM platform_document_placements
                    WHERE workspace_id = ?
                    ORDER BY updated_at DESC, placement_id
                    LIMIT ?
                    """,
                    (workspace_id, max(1, min(int(limit), 500))),
                ).fetchall()
        return tuple(self._placement(row) for row in rows)

    def delete_placement(self, placement_id: str) -> bool:
        placement_id = _validate_placement_id(placement_id)
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM platform_document_placements WHERE placement_id = ?",
                (placement_id,),
            )
            connection.commit()
            return cursor.rowcount == 1

    def create_full_text_grant(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        article_id: str,
        artifact_id: str | None,
        provider_record_id: str,
        access_type: str,
        license_text: str,
        access_url: str,
        cache_path: str,
        redistribution_allowed: bool,
        expires_at: datetime | None,
        created_by: str,
    ) -> FullTextAccessGrant:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(created_by, "user")
        if project_id is not None:
            require_opaque_id(project_id, "project")
        kind = str(access_type or "").strip()
        if not kind:
            raise ValueError("access_type is required")
        grant_id = _grant_id()
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO platform_full_text_access_grants(
                    grant_id, workspace_id, project_id, article_id, artifact_id,
                    provider_record_id, access_type, license_text, access_url,
                    cache_path, redistribution_allowed, expires_at, created_by,
                    created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    grant_id,
                    workspace_id,
                    project_id,
                    article_id,
                    artifact_id,
                    str(provider_record_id or ""),
                    kind,
                    str(license_text or "")[:500],
                    str(access_url or "")[:2000],
                    str(cache_path or "")[:4000],
                    1 if redistribution_allowed else 0,
                    _iso(expires_at) if expires_at else None,
                    created_by,
                    _iso(now),
                    _iso(now),
                ),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM platform_full_text_access_grants WHERE grant_id = ?",
                (grant_id,),
            ).fetchone()
        if row is None:
            raise EvidenceLibraryError("full-text grant disappeared after insert")
        return self._grant(row)

    def get_full_text_grant(self, grant_id: str) -> FullTextAccessGrant | None:
        try:
            grant_id = _validate_grant_id(grant_id)
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_full_text_access_grants WHERE grant_id = ?",
                (grant_id,),
            ).fetchone()
        return self._grant(row) if row is not None else None

    def active_full_text_grants(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        article_id: str,
    ) -> tuple[FullTextAccessGrant, ...]:
        now = _iso(_now())
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM platform_full_text_access_grants
                WHERE workspace_id = ? AND article_id = ?
                  AND (project_id IS NULL OR project_id = ?)
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC, grant_id
                """,
                (workspace_id, article_id, project_id, now),
            ).fetchall()
        return tuple(self._grant(row) for row in rows)


class EvidenceLibraryService:
    """Tenant authorization boundary over private placements and global documents."""

    def __init__(
        self,
        store: SQLiteEvidenceLibraryStore,
        registry: GlobalEvidenceRegistryReader,
        workspace_service: WorkspaceProjectService,
        *,
        permission_service: PermissionService | None = None,
    ) -> None:
        self.store = store
        self.registry = registry
        self.workspace_service = workspace_service
        self.permission_service = permission_service or PermissionService()

    def _context(
        self,
        principal: Principal,
        current: ResearchContext,
        *,
        permission: Permission,
        project_id: str | None,
    ) -> AuthorizationContext:
        if current.workspace_id is None:
            raise PermissionError("workspace_context_required")
        auth = self.workspace_service.authorization_context(
            principal,
            workspace_id=current.workspace_id,
            project_id=project_id,
        )
        self.permission_service.require(principal, permission, context=auth)
        return auth

    @staticmethod
    def _target_project(current: ResearchContext, scope: str) -> str | None:
        normalized = str(scope or "workspace").strip().casefold()
        if normalized == "workspace":
            return None
        if normalized == "project":
            if current.project_id is None:
                raise PermissionError("project_context_required")
            return current.project_id
        raise ValueError("invalid library scope")

    def save(
        self,
        principal: Principal,
        current: ResearchContext,
        *,
        article_id: str,
        scope: str = "workspace",
        state: str = "not_screened",
        tags: list[str] | tuple[str, ...] | None = None,
        notes: str = "",
    ) -> EvidenceLibraryEntry:
        project_id = self._target_project(current, scope)
        self._context(
            principal,
            current,
            permission=Permission.EVIDENCE_LIBRARY_WRITE,
            project_id=project_id,
        )
        document = self.registry.get(article_id)
        if document is None:
            raise KeyError(article_id)
        assert current.workspace_id is not None
        placement = self.store.upsert_placement(
            workspace_id=current.workspace_id,
            project_id=project_id,
            article_id=document.article_id,
            state=_state(state),
            tags=_tags(tags),
            notes=_note(notes),
            created_by=principal.user_id,
        )
        return EvidenceLibraryEntry(placement=placement, document=document)

    def list(
        self,
        principal: Principal,
        current: ResearchContext,
        *,
        scope: str = "workspace",
        limit: int = 200,
    ) -> tuple[EvidenceLibraryEntry, ...]:
        project_id = self._target_project(current, scope)
        self._context(
            principal,
            current,
            permission=Permission.EVIDENCE_LIBRARY_READ,
            project_id=project_id,
        )
        assert current.workspace_id is not None
        placements = self.store.list_placements(
            workspace_id=current.workspace_id,
            project_id=project_id,
            project_only=project_id is not None,
            limit=limit,
        )
        documents = self.registry.get_many(tuple(item.article_id for item in placements))
        return tuple(
            EvidenceLibraryEntry(placement=item, document=documents[item.article_id])
            for item in placements
            if item.article_id in documents
        )

    def require_placement(
        self,
        principal: Principal,
        current: ResearchContext,
        placement_id: str,
        *,
        write: bool = False,
    ) -> EvidenceLibraryEntry:
        placement = self.store.get_placement(placement_id)
        if placement is None or current.workspace_id != placement.workspace_id:
            raise KeyError(placement_id)
        self._context(
            principal,
            current,
            permission=(
                Permission.EVIDENCE_LIBRARY_WRITE
                if write
                else Permission.EVIDENCE_LIBRARY_READ
            ),
            project_id=placement.project_id,
        )
        document = self.registry.get(placement.article_id)
        if document is None:
            raise EvidenceLibraryError("placement references missing global document")
        return EvidenceLibraryEntry(placement=placement, document=document)

    def delete(
        self,
        principal: Principal,
        current: ResearchContext,
        placement_id: str,
    ) -> bool:
        self.require_placement(principal, current, placement_id, write=True)
        return self.store.delete_placement(placement_id)

    def create_full_text_grant(
        self,
        principal: Principal,
        current: ResearchContext,
        *,
        article_id: str,
        scope: str = "workspace",
        artifact_id: str | None = None,
        provider_record_id: str = "",
        access_type: str,
        license_text: str = "",
        access_url: str = "",
        cache_path: str = "",
        redistribution_allowed: bool = False,
        expires_at: datetime | None = None,
    ) -> FullTextAccessGrant:
        project_id = self._target_project(current, scope)
        self._context(
            principal,
            current,
            permission=Permission.FULL_TEXT_ACCESS_MANAGE,
            project_id=project_id,
        )
        document = self.registry.get(article_id)
        if document is None:
            raise KeyError(article_id)
        assert current.workspace_id is not None
        return self.store.create_full_text_grant(
            workspace_id=current.workspace_id,
            project_id=project_id,
            article_id=document.article_id,
            artifact_id=artifact_id,
            provider_record_id=provider_record_id,
            access_type=access_type,
            license_text=license_text,
            access_url=access_url,
            cache_path=cache_path,
            redistribution_allowed=redistribution_allowed,
            expires_at=expires_at,
            created_by=principal.user_id,
        )

    def full_text_access(
        self,
        principal: Principal,
        current: ResearchContext,
        article_id: str,
    ) -> tuple[FullTextAccessGrant, ...]:
        self._context(
            principal,
            current,
            permission=Permission.FULL_TEXT_ACCESS_READ,
            project_id=current.project_id,
        )
        if self.registry.get(article_id) is None:
            raise KeyError(article_id)
        assert current.workspace_id is not None
        return self.store.active_full_text_grants(
            workspace_id=current.workspace_id,
            project_id=current.project_id,
            article_id=article_id,
        )
