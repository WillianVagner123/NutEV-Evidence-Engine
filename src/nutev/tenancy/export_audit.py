from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sqlite3
from typing import Any, Iterable
from uuid import uuid4

from .access import WorkspaceProjectService
from .applications import SQLiteApplicationStore
from .models import Principal, require_opaque_id
from .permissions import AuthorizationContext, Permission, PermissionService

EXPORT_AUDIT_SCHEMA_VERSION = 1
MAX_EXPORT_ARTIFACTS = 100
MAX_EXPORT_ARTIFACT_BYTES = 25 * 1024 * 1024
MAX_EXPORT_TOTAL_BYTES = 100 * 1024 * 1024
_ALLOWED_MEDIA_TYPES = frozenset(
    {
        "application/json",
        "application/x-ndjson",
        "text/csv",
        "text/markdown",
        "text/plain",
        "text/tab-separated-values",
    }
)
_SAFE_ARTIFACT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SAFE_KIND_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
_EXPORT_ID_RE = re.compile(r"^exp_[a-f0-9]{32}$")
_AUDIT_ID_RE = re.compile(r"^aud_[a-f0-9]{32}$")


class ExportAuditError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return _now()
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _new_export_id() -> str:
    return f"exp_{uuid4().hex}"


def _new_audit_id() -> str:
    return f"aud_{uuid4().hex}"


def _require_export_id(value: str) -> str:
    text = str(value or "")
    if not _EXPORT_ID_RE.fullmatch(text):
        raise ValueError("invalid export_id")
    return text


def _require_audit_id(value: str) -> str:
    text = str(value or "")
    if not _AUDIT_ID_RE.fullmatch(text):
        raise ValueError("invalid audit_event_id")
    return text


def _clean_export_kind(value: str) -> str:
    text = str(value or "").strip()
    if not _SAFE_KIND_RE.fullmatch(text):
        raise ValueError("invalid export_kind")
    return text


def _clean_artifact_name(value: str) -> str:
    text = str(value or "").strip()
    if not _SAFE_ARTIFACT_RE.fullmatch(text):
        raise ValueError("invalid artifact name")
    if text in {".", ".."} or "/" in text or "\\" in text:
        raise ValueError("invalid artifact name")
    return text


def _clean_media_type(value: str) -> str:
    text = str(value or "").strip().casefold()
    if text not in _ALLOWED_MEDIA_TYPES:
        raise ValueError("unsupported export media_type")
    return text


def _safe_metadata(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("export metadata must be an object")
    encoded = _canonical_json(value)
    if len(encoded.encode("utf-8")) > 64 * 1024:
        raise ValueError("export metadata is too large")
    parsed = json.loads(encoded)
    if not isinstance(parsed, dict):
        raise ValueError("export metadata must be an object")
    return parsed


def _atomic_bytes(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    tmp.write_bytes(payload)
    tmp.replace(path)
    return sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class ExportArtifactInput:
    name: str
    media_type: str
    content: bytes

    def __post_init__(self) -> None:
        _clean_artifact_name(self.name)
        _clean_media_type(self.media_type)
        if not isinstance(self.content, bytes):
            raise ValueError("export artifact content must be bytes")
        if len(self.content) > MAX_EXPORT_ARTIFACT_BYTES:
            raise ValueError("export artifact exceeds size limit")


@dataclass(frozen=True, slots=True)
class ProjectExportArtifact:
    export_id: str
    name: str
    media_type: str
    sha256: str
    size_bytes: int
    relative_path: str

    def descriptor(self) -> dict[str, object]:
        return {
            "name": self.name,
            "media_type": self.media_type,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class ProjectExport:
    id: str
    workspace_id: str
    project_id: str
    application_id: str | None
    export_kind: str
    created_by: str
    manifest_sha256: str
    artifact_count: int
    total_bytes: int
    created_at: datetime

    def descriptor(self) -> dict[str, object]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "application_id": self.application_id,
            "export_kind": self.export_kind,
            "created_by": self.created_by,
            "manifest_sha256": self.manifest_sha256,
            "artifact_count": self.artifact_count,
            "total_bytes": self.total_bytes,
            "created_at": _iso(self.created_at),
        }


@dataclass(frozen=True, slots=True)
class ProjectAuditEvent:
    seq: int
    event_id: str
    workspace_id: str
    project_id: str
    application_id: str | None
    actor_user_id: str
    event_type: str
    resource_type: str
    resource_id: str
    details: dict[str, Any]
    previous_event_hash: str | None
    event_hash: str
    created_at: datetime

    def descriptor(self) -> dict[str, object]:
        return {
            "seq": self.seq,
            "event_id": self.event_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "application_id": self.application_id,
            "actor_user_id": self.actor_user_id,
            "event_type": self.event_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": dict(self.details),
            "previous_event_hash": self.previous_event_hash,
            "event_hash": self.event_hash,
            "created_at": _iso(self.created_at),
        }


class SQLiteProjectExportAuditStore:
    """Private export metadata and append-only project audit chain."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        self._apply_schema(connection)
        return connection

    @staticmethod
    def _apply_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS platform_export_audit_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS platform_project_exports (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                application_id TEXT,
                export_kind TEXT NOT NULL,
                created_by TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                manifest_sha256 TEXT NOT NULL,
                artifact_count INTEGER NOT NULL,
                total_bytes INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_platform_project_exports_scope
                ON platform_project_exports(workspace_id, project_id, created_at, id);

            CREATE TABLE IF NOT EXISTS platform_project_export_artifacts (
                export_id TEXT NOT NULL REFERENCES platform_project_exports(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                media_type TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                relative_path TEXT NOT NULL,
                PRIMARY KEY(export_id, name)
            );

            CREATE TABLE IF NOT EXISTS platform_project_audit_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                workspace_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                application_id TEXT,
                actor_user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                details_json TEXT NOT NULL,
                previous_event_hash TEXT,
                event_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_platform_project_audit_scope
                ON platform_project_audit_events(workspace_id, project_id, seq);
            """
        )
        connection.execute(
            "INSERT INTO platform_export_audit_meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(EXPORT_AUDIT_SCHEMA_VERSION),),
        )
        connection.commit()

    @staticmethod
    def _export_from_row(row: sqlite3.Row) -> ProjectExport:
        return ProjectExport(
            id=str(row["id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            application_id=str(row["application_id"]) if row["application_id"] else None,
            export_kind=str(row["export_kind"]),
            created_by=str(row["created_by"]),
            manifest_sha256=str(row["manifest_sha256"]),
            artifact_count=int(row["artifact_count"]),
            total_bytes=int(row["total_bytes"]),
            created_at=_parse_datetime(str(row["created_at"])),
        )

    @staticmethod
    def _artifact_from_row(row: sqlite3.Row) -> ProjectExportArtifact:
        return ProjectExportArtifact(
            export_id=str(row["export_id"]),
            name=str(row["name"]),
            media_type=str(row["media_type"]),
            sha256=str(row["sha256"]),
            size_bytes=int(row["size_bytes"]),
            relative_path=str(row["relative_path"]),
        )

    @staticmethod
    def _event_from_row(row: sqlite3.Row) -> ProjectAuditEvent:
        details = json.loads(str(row["details_json"] or "{}"))
        if not isinstance(details, dict):
            raise ExportAuditError("invalid audit event details")
        return ProjectAuditEvent(
            seq=int(row["seq"]),
            event_id=str(row["event_id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            application_id=str(row["application_id"]) if row["application_id"] else None,
            actor_user_id=str(row["actor_user_id"]),
            event_type=str(row["event_type"]),
            resource_type=str(row["resource_type"]),
            resource_id=str(row["resource_id"]),
            details=details,
            previous_event_hash=str(row["previous_event_hash"]) if row["previous_event_hash"] else None,
            event_hash=str(row["event_hash"]),
            created_at=_parse_datetime(str(row["created_at"])),
        )

    @staticmethod
    def _event_hash(
        *,
        event_id: str,
        workspace_id: str,
        project_id: str,
        application_id: str | None,
        actor_user_id: str,
        event_type: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any],
        previous_event_hash: str | None,
        created_at: str,
    ) -> str:
        payload = {
            "event_id": event_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "application_id": application_id,
            "actor_user_id": actor_user_id,
            "event_type": event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "previous_event_hash": previous_event_hash,
            "created_at": created_at,
        }
        return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()

    def _append_event(
        self,
        connection: sqlite3.Connection,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str | None,
        actor_user_id: str,
        event_type: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any],
    ) -> None:
        previous = connection.execute(
            """
            SELECT event_hash FROM platform_project_audit_events
            WHERE workspace_id = ? AND project_id = ?
            ORDER BY seq DESC LIMIT 1
            """,
            (workspace_id, project_id),
        ).fetchone()
        previous_hash = str(previous["event_hash"]) if previous is not None else None
        event_id = _new_audit_id()
        created_at = _iso(_now())
        event_hash = self._event_hash(
            event_id=event_id,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            previous_event_hash=previous_hash,
            created_at=created_at,
        )
        connection.execute(
            """
            INSERT INTO platform_project_audit_events(
                event_id, workspace_id, project_id, application_id, actor_user_id,
                event_type, resource_type, resource_id, details_json,
                previous_event_hash, event_hash, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                event_id,
                workspace_id,
                project_id,
                application_id,
                actor_user_id,
                event_type,
                resource_type,
                resource_id,
                _canonical_json(details),
                previous_hash,
                event_hash,
                created_at,
            ),
        )

    def persist_export(
        self,
        export: ProjectExport,
        artifacts: Iterable[ProjectExportArtifact],
        manifest: dict[str, Any],
    ) -> ProjectExport:
        artifact_rows = tuple(artifacts)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO platform_project_exports(
                    id, workspace_id, project_id, application_id, export_kind,
                    created_by, manifest_json, manifest_sha256, artifact_count,
                    total_bytes, created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    export.id,
                    export.workspace_id,
                    export.project_id,
                    export.application_id,
                    export.export_kind,
                    export.created_by,
                    _canonical_json(manifest),
                    export.manifest_sha256,
                    export.artifact_count,
                    export.total_bytes,
                    _iso(export.created_at),
                ),
            )
            for artifact in artifact_rows:
                connection.execute(
                    """
                    INSERT INTO platform_project_export_artifacts(
                        export_id, name, media_type, sha256, size_bytes, relative_path
                    ) VALUES(?,?,?,?,?,?)
                    """,
                    (
                        artifact.export_id,
                        artifact.name,
                        artifact.media_type,
                        artifact.sha256,
                        artifact.size_bytes,
                        artifact.relative_path,
                    ),
                )
            self._append_event(
                connection,
                workspace_id=export.workspace_id,
                project_id=export.project_id,
                application_id=export.application_id,
                actor_user_id=export.created_by,
                event_type="export_created",
                resource_type="project_export",
                resource_id=export.id,
                details={
                    "manifest_sha256": export.manifest_sha256,
                    "artifact_count": export.artifact_count,
                    "total_bytes": export.total_bytes,
                    "export_kind": export.export_kind,
                },
            )
            connection.commit()
        saved = self.get_export(export.workspace_id, export.project_id, export.id)
        if saved is None:
            raise ExportAuditError("export disappeared after persist")
        return saved

    def list_exports(self, workspace_id: str, project_id: str) -> tuple[ProjectExport, ...]:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM platform_project_exports
                WHERE workspace_id = ? AND project_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (workspace_id, project_id),
            ).fetchall()
        return tuple(self._export_from_row(row) for row in rows)

    def get_export(self, workspace_id: str, project_id: str, export_id: str) -> ProjectExport | None:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        _require_export_id(export_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM platform_project_exports
                WHERE workspace_id = ? AND project_id = ? AND id = ?
                """,
                (workspace_id, project_id, export_id),
            ).fetchone()
        return self._export_from_row(row) if row is not None else None

    def manifest(self, workspace_id: str, project_id: str, export_id: str) -> dict[str, Any]:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        _require_export_id(export_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT manifest_json FROM platform_project_exports
                WHERE workspace_id = ? AND project_id = ? AND id = ?
                """,
                (workspace_id, project_id, export_id),
            ).fetchone()
        if row is None:
            raise KeyError(export_id)
        parsed = json.loads(str(row["manifest_json"]))
        if not isinstance(parsed, dict):
            raise ExportAuditError("invalid export manifest")
        return parsed

    def artifacts(self, workspace_id: str, project_id: str, export_id: str) -> tuple[ProjectExportArtifact, ...]:
        if self.get_export(workspace_id, project_id, export_id) is None:
            raise KeyError(export_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT a.* FROM platform_project_export_artifacts a
                JOIN platform_project_exports e ON e.id = a.export_id
                WHERE e.workspace_id = ? AND e.project_id = ? AND e.id = ?
                ORDER BY a.name
                """,
                (workspace_id, project_id, export_id),
            ).fetchall()
        return tuple(self._artifact_from_row(row) for row in rows)

    def artifact(self, workspace_id: str, project_id: str, export_id: str, name: str) -> ProjectExportArtifact:
        clean_name = _clean_artifact_name(name)
        if self.get_export(workspace_id, project_id, export_id) is None:
            raise KeyError(export_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT a.* FROM platform_project_export_artifacts a
                JOIN platform_project_exports e ON e.id = a.export_id
                WHERE e.workspace_id = ? AND e.project_id = ? AND e.id = ? AND a.name = ?
                """,
                (workspace_id, project_id, export_id, clean_name),
            ).fetchone()
        if row is None:
            raise KeyError(clean_name)
        return self._artifact_from_row(row)

    def record_artifact_read(
        self,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str | None,
        actor_user_id: str,
        export_id: str,
        artifact: ProjectExportArtifact,
    ) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._append_event(
                connection,
                workspace_id=workspace_id,
                project_id=project_id,
                application_id=application_id,
                actor_user_id=actor_user_id,
                event_type="export_artifact_read",
                resource_type="project_export_artifact",
                resource_id=f"{export_id}:{artifact.name}",
                details={
                    "sha256": artifact.sha256,
                    "size_bytes": artifact.size_bytes,
                    "media_type": artifact.media_type,
                },
            )
            connection.commit()

    def audit_events(self, workspace_id: str, project_id: str, *, limit: int = 200) -> tuple[ProjectAuditEvent, ...]:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        bounded = max(1, min(int(limit), 1000))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM platform_project_audit_events
                WHERE workspace_id = ? AND project_id = ?
                ORDER BY seq ASC
                LIMIT ?
                """,
                (workspace_id, project_id, bounded),
            ).fetchall()
        return tuple(self._event_from_row(row) for row in rows)

    def verify_audit_chain(self, workspace_id: str, project_id: str) -> bool:
        events = self.audit_events(workspace_id, project_id, limit=1000)
        previous_hash: str | None = None
        for event in events:
            if event.previous_event_hash != previous_hash:
                return False
            expected = self._event_hash(
                event_id=event.event_id,
                workspace_id=event.workspace_id,
                project_id=event.project_id,
                application_id=event.application_id,
                actor_user_id=event.actor_user_id,
                event_type=event.event_type,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                details=event.details,
                previous_event_hash=event.previous_event_hash,
                created_at=_iso(event.created_at),
            )
            if expected != event.event_hash:
                return False
            previous_hash = event.event_hash
        return True


class ProjectExportAuditService:
    """Tenant-scoped custody for already-produced export artifacts.

    This layer does not infer or produce scientific findings. It only authorizes,
    stores, hashes, manifests, and audits artifacts supplied by a scientific or
    application-specific exporter.
    """

    def __init__(
        self,
        store: SQLiteProjectExportAuditStore,
        export_root: Path,
        access: WorkspaceProjectService,
        *,
        applications: SQLiteApplicationStore | None = None,
        permissions: PermissionService | None = None,
    ) -> None:
        self.store = store
        self.export_root = Path(export_root).expanduser().resolve()
        self.access = access
        self.applications = applications
        self.permissions = permissions or PermissionService()

    def _context(
        self,
        principal: Principal,
        workspace_id: str,
        project_id: str,
        *,
        policy_grants: frozenset[Permission] = frozenset(),
    ) -> AuthorizationContext:
        self.access.require_project(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        return self.access.authorization_context(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            policy_grants=policy_grants,
        )

    def _application_id(self, project_id: str) -> str | None:
        if self.applications is None:
            return None
        instance = self.applications.get_for_project(project_id)
        return instance.application.id if instance is not None else None

    def _export_directory(self, workspace_id: str, project_id: str, export_id: str) -> Path:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        _require_export_id(export_id)
        root = self.export_root
        target = (root / workspace_id / project_id / export_id).resolve()
        if root != target and root not in target.parents:
            raise ExportAuditError("export path escaped configured root")
        return target

    def create_export(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        export_kind: str,
        artifacts: Iterable[ExportArtifactInput],
        metadata: dict[str, Any] | None = None,
        policy_grants: frozenset[Permission] = frozenset(),
    ) -> ProjectExport:
        context = self._context(
            principal,
            workspace_id,
            project_id,
            policy_grants=policy_grants,
        )
        self.permissions.require(principal, Permission.EXPORT, context=context)
        kind = _clean_export_kind(export_kind)
        meta = _safe_metadata(metadata)
        inputs = tuple(artifacts)
        if not inputs:
            raise ValueError("at least one export artifact is required")
        if len(inputs) > MAX_EXPORT_ARTIFACTS:
            raise ValueError("too many export artifacts")
        names = [_clean_artifact_name(item.name) for item in inputs]
        if len(names) != len(set(names)):
            raise ValueError("duplicate export artifact name")
        total_bytes = sum(len(item.content) for item in inputs)
        if total_bytes > MAX_EXPORT_TOTAL_BYTES:
            raise ValueError("export exceeds total size limit")

        export_id = _new_export_id()
        created_at = _now()
        application_id = self._application_id(project_id)
        directory = self._export_directory(workspace_id, project_id, export_id)
        if directory.exists():
            raise ExportAuditError("export directory already exists")

        artifact_records: list[ProjectExportArtifact] = []
        try:
            directory.mkdir(parents=True, exist_ok=False)
            for item in inputs:
                name = _clean_artifact_name(item.name)
                media_type = _clean_media_type(item.media_type)
                digest = _atomic_bytes(directory / name, item.content)
                artifact_records.append(
                    ProjectExportArtifact(
                        export_id=export_id,
                        name=name,
                        media_type=media_type,
                        sha256=digest,
                        size_bytes=len(item.content),
                        relative_path=name,
                    )
                )

            manifest = {
                "schema_version": EXPORT_AUDIT_SCHEMA_VERSION,
                "export_type": "NUTEV_TENANT_PROJECT_EXPORT",
                "export_id": export_id,
                "workspace_id": workspace_id,
                "project_id": project_id,
                "application_id": application_id,
                "export_kind": kind,
                "created_by": principal.user_id,
                "created_at": _iso(created_at),
                "metadata": meta,
                "artifacts": [record.descriptor() for record in artifact_records],
                "assertions": {
                    "tenant_scoped": True,
                    "project_scoped": True,
                    "absolute_storage_paths_exposed": False,
                    "scientific_semantics_inferred": False,
                },
            }
            manifest_bytes = (_canonical_json(manifest) + "\n").encode("utf-8")
            manifest_sha = _atomic_bytes(directory / "MANIFEST.json", manifest_bytes)
            export = ProjectExport(
                id=export_id,
                workspace_id=workspace_id,
                project_id=project_id,
                application_id=application_id,
                export_kind=kind,
                created_by=principal.user_id,
                manifest_sha256=manifest_sha,
                artifact_count=len(artifact_records),
                total_bytes=total_bytes,
                created_at=created_at,
            )
            return self.store.persist_export(export, artifact_records, manifest)
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise

    def list_exports(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
    ) -> tuple[ProjectExport, ...]:
        context = self._context(principal, workspace_id, project_id)
        self.permissions.require(principal, Permission.PROJECT_AUDIT_READ, context=context)
        return self.store.list_exports(workspace_id, project_id)

    def manifest(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        export_id: str,
    ) -> dict[str, Any]:
        context = self._context(principal, workspace_id, project_id)
        self.permissions.require(principal, Permission.PROJECT_AUDIT_READ, context=context)
        return self.store.manifest(workspace_id, project_id, export_id)

    def read_artifact(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        export_id: str,
        name: str,
        policy_grants: frozenset[Permission] = frozenset(),
    ) -> tuple[ProjectExportArtifact, bytes]:
        context = self._context(
            principal,
            workspace_id,
            project_id,
            policy_grants=policy_grants,
        )
        self.permissions.require(principal, Permission.EXPORT, context=context)
        export = self.store.get_export(workspace_id, project_id, export_id)
        if export is None:
            raise KeyError(export_id)
        artifact = self.store.artifact(workspace_id, project_id, export_id, name)
        directory = self._export_directory(workspace_id, project_id, export_id)
        path = (directory / artifact.relative_path).resolve()
        if directory not in path.parents:
            raise ExportAuditError("artifact path escaped export directory")
        if not path.is_file():
            raise FileNotFoundError(artifact.name)
        payload = path.read_bytes()
        actual = sha256(payload).hexdigest()
        if actual != artifact.sha256 or len(payload) != artifact.size_bytes:
            raise ExportAuditError("export artifact integrity mismatch")
        self.store.record_artifact_read(
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=export.application_id,
            actor_user_id=principal.user_id,
            export_id=export_id,
            artifact=artifact,
        )
        return artifact, payload

    def audit_events(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        limit: int = 200,
    ) -> tuple[ProjectAuditEvent, ...]:
        context = self._context(principal, workspace_id, project_id)
        self.permissions.require(principal, Permission.PROJECT_AUDIT_READ, context=context)
        return self.store.audit_events(workspace_id, project_id, limit=limit)

    def audit_chain_valid(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
    ) -> bool:
        context = self._context(principal, workspace_id, project_id)
        self.permissions.require(principal, Permission.PROJECT_AUDIT_READ, context=context)
        return self.store.verify_audit_chain(workspace_id, project_id)
