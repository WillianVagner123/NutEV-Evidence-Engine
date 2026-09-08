from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable

from .access import WorkspaceProjectService
from .models import Principal, ResearchApplication, new_opaque_id, require_opaque_id
from .permissions import AuthorizationContext, Permission, PermissionService

APPLICATION_SCHEMA_VERSION = 1

GENERIC_EVIDENCE_PROJECT = "GENERIC_EVIDENCE_PROJECT"
SCOPING_REVIEW = "SCOPING_REVIEW"
INTEGRATIVE_REVIEW = "INTEGRATIVE_REVIEW"


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


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("application configuration must be a JSON object")
    return parsed


def _clean_token(value: str, field: str) -> str:
    token = str(value or "").strip()
    if not token:
        raise ValueError(f"{field} is required")
    if len(token) > 120:
        raise ValueError(f"{field} is too long")
    return token


@dataclass(frozen=True, slots=True)
class ApplicationTemplate:
    """Reusable, public application recipe without project-specific scientific state."""

    template_id: str
    version: str
    name: str
    application_type: str
    components: tuple[str, ...]
    defaults_json: str = "{}"
    description: str = ""
    visibility: str = "PUBLIC"

    def __post_init__(self) -> None:
        _clean_token(self.template_id, "template_id")
        _clean_token(self.version, "template version")
        _clean_token(self.name, "template name")
        _clean_token(self.application_type, "application_type")
        if self.visibility != "PUBLIC":
            raise ValueError("built-in application templates must be PUBLIC")
        if not self.components:
            raise ValueError("template components are required")
        if len(set(self.components)) != len(self.components):
            raise ValueError("template components must be unique")
        for component in self.components:
            _clean_token(component, "template component")
        _object(self.defaults_json)

    def defaults(self) -> dict[str, Any]:
        """Return a detached copy so project config can never mutate the template."""
        return _object(self.defaults_json)

    def descriptor(self) -> dict[str, object]:
        return {
            "template_id": self.template_id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "application_type": self.application_type,
            "components": list(self.components),
            "defaults": self.defaults(),
            "visibility": self.visibility,
        }


BUILTIN_APPLICATION_TEMPLATES: tuple[ApplicationTemplate, ...] = (
    ApplicationTemplate(
        template_id=GENERIC_EVIDENCE_PROJECT,
        version="1.0",
        name="Generic Evidence Project",
        application_type=GENERIC_EVIDENCE_PROJECT,
        description="Composable evidence workspace without a review-method mandate.",
        components=(
            "RESEARCH_QUESTION",
            "SEARCH",
            "NORMALIZE",
            "TRACEABILITY",
            "DEDUPLICATE",
            "ORGANIZE",
            "HUMAN_VERIFICATION",
            "SYNTHESIS",
        ),
        defaults_json=_json({"framework": None, "reporting_profile": None}),
    ),
    ApplicationTemplate(
        template_id=SCOPING_REVIEW,
        version="1.0",
        name="Scoping Review",
        application_type=SCOPING_REVIEW,
        description="Composable scoping-review starter; project methods remain configurable.",
        components=(
            "PCC",
            "SEARCH",
            "DEDUPLICATION",
            "TITLE_ABSTRACT_SCREENING",
            "FULL_TEXT",
            "EXTRACTION",
            "HUMAN_VERIFICATION",
            "SYNTHESIS",
            "PRISMA_SCR",
        ),
        defaults_json=_json({"framework": "PCC", "reporting_profile": "PRISMA-ScR"}),
    ),
    ApplicationTemplate(
        template_id=INTEGRATIVE_REVIEW,
        version="1.0",
        name="Integrative Review",
        application_type=INTEGRATIVE_REVIEW,
        description="Composable integrative-review starter with project-owned methodological config.",
        components=(
            "RESEARCH_QUESTION",
            "SEARCH",
            "DEDUPLICATION",
            "TITLE_ABSTRACT_SCREENING",
            "FULL_TEXT",
            "EXTRACTION",
            "HUMAN_VERIFICATION",
            "SYNTHESIS",
        ),
        defaults_json=_json({"framework": None, "reporting_profile": None}),
    ),
)


class ApplicationTemplateCatalog:
    """Version-aware catalog; custom templates may be injected without changing the Engine enum."""

    def __init__(self, templates: Iterable[ApplicationTemplate] = BUILTIN_APPLICATION_TEMPLATES) -> None:
        indexed: dict[tuple[str, str], ApplicationTemplate] = {}
        for template in templates:
            key = (template.template_id, template.version)
            if key in indexed:
                raise ValueError(f"duplicate application template: {template.template_id}@{template.version}")
            indexed[key] = template
        self._templates = indexed

    def list(self) -> tuple[ApplicationTemplate, ...]:
        return tuple(sorted(self._templates.values(), key=lambda item: (item.template_id, item.version)))

    def get(self, template_id: str, version: str | None = None) -> ApplicationTemplate | None:
        tid = str(template_id or "").strip()
        if not tid:
            return None
        if version is not None:
            return self._templates.get((tid, str(version).strip()))
        matches = [item for (candidate, _), item in self._templates.items() if candidate == tid]
        if not matches:
            return None
        return sorted(matches, key=lambda item: item.version)[-1]


@dataclass(frozen=True, slots=True)
class ApplicationInstance:
    application: ResearchApplication
    template_version: str | None
    configuration_json: str
    created_by: str
    updated_at: datetime

    def __post_init__(self) -> None:
        require_opaque_id(self.created_by, "user")
        _object(self.configuration_json)

    def configuration(self) -> dict[str, Any]:
        return _object(self.configuration_json)

    def descriptor(self) -> dict[str, object]:
        app = self.application
        return {
            "id": app.id,
            "project_id": app.project_id,
            "application_type": app.application_type,
            "template_id": app.template_id,
            "template_version": self.template_version,
            "config_version": app.config_version,
            "configuration": self.configuration(),
            "status": app.status,
            "created_at": app.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ApplicationDataError(RuntimeError):
    pass


def _apply_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS platform_application_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS platform_research_applications (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL UNIQUE,
            application_type TEXT NOT NULL,
            template_id TEXT,
            template_version TEXT,
            config_version TEXT NOT NULL,
            configuration_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active', 'archived')),
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_platform_research_applications_project
            ON platform_research_applications(project_id, status);
        """
    )
    connection.execute(
        "INSERT INTO platform_application_meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(APPLICATION_SCHEMA_VERSION),),
    )
    connection.commit()


class SQLiteApplicationStore:
    """Private project-application persistence; templates themselves remain reusable/public."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path).resolve()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        _apply_schema(connection)
        return connection

    @staticmethod
    def _instance(row: sqlite3.Row) -> ApplicationInstance:
        application = ResearchApplication(
            id=str(row["id"]),
            project_id=str(row["project_id"]),
            application_type=str(row["application_type"]),
            template_id=str(row["template_id"]) if row["template_id"] else None,
            config_version=str(row["config_version"]),
            status=str(row["status"]),
            created_at=_parse_datetime(str(row["created_at"])),
        )
        return ApplicationInstance(
            application=application,
            template_version=str(row["template_version"]) if row["template_version"] else None,
            configuration_json=str(row["configuration_json"] or "{}"),
            created_by=str(row["created_by"]),
            updated_at=_parse_datetime(str(row["updated_at"])),
        )

    def get_for_project(self, project_id: str) -> ApplicationInstance | None:
        try:
            require_opaque_id(project_id, "project")
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_research_applications WHERE project_id = ? AND status = 'active'",
                (project_id,),
            ).fetchone()
        return self._instance(row) if row is not None else None

    def save(
        self,
        *,
        project_id: str,
        application_type: str,
        template_id: str | None,
        template_version: str | None,
        config_version: str,
        configuration: dict[str, Any],
        actor_user_id: str,
    ) -> ApplicationInstance:
        require_opaque_id(project_id, "project")
        require_opaque_id(actor_user_id, "user")
        kind = _clean_token(application_type, "application_type")
        version = _clean_token(config_version, "config_version")
        if template_id is not None:
            _clean_token(template_id, "template_id")
        if template_version is not None:
            _clean_token(template_version, "template_version")
        payload = _json(configuration)
        _object(payload)
        now = _now()
        existing = self.get_for_project(project_id)
        if existing is None:
            application_id = new_opaque_id("application")
            created_at = now
        else:
            application_id = existing.application.id
            created_at = existing.application.created_at
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO platform_research_applications(
                    id, project_id, application_type, template_id, template_version,
                    config_version, configuration_json, status, created_by, created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,'active',?,?,?)
                ON CONFLICT(project_id) DO UPDATE SET
                    application_type=excluded.application_type,
                    template_id=excluded.template_id,
                    template_version=excluded.template_version,
                    config_version=excluded.config_version,
                    configuration_json=excluded.configuration_json,
                    status='active',
                    updated_at=excluded.updated_at
                """,
                (
                    application_id,
                    project_id,
                    kind,
                    template_id,
                    template_version,
                    version,
                    payload,
                    actor_user_id,
                    _iso(created_at),
                    _iso(now),
                ),
            )
            connection.commit()
        saved = self.get_for_project(project_id)
        if saved is None:
            raise ApplicationDataError("application disappeared after save")
        return saved


class ApplicationService:
    """Project-scoped application boundary with reusable templates and private configuration."""

    def __init__(
        self,
        store: SQLiteApplicationStore,
        access: WorkspaceProjectService,
        *,
        catalog: ApplicationTemplateCatalog | None = None,
        permissions: PermissionService | None = None,
    ) -> None:
        self.store = store
        self.access = access
        self.catalog = catalog or ApplicationTemplateCatalog()
        self.permissions = permissions or PermissionService()

    def list_templates(self) -> tuple[ApplicationTemplate, ...]:
        return self.catalog.list()

    def _context(self, principal: Principal, workspace_id: str, project_id: str) -> AuthorizationContext:
        self.access.require_project(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        return self.access.authorization_context(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )

    def get(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
    ) -> ApplicationInstance | None:
        context = self._context(principal, workspace_id, project_id)
        self.permissions.require(principal, Permission.APPLICATION_READ, context=context)
        return self.store.get_for_project(project_id)

    def configure(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        application_type: str | None = None,
        template_id: str | None = None,
        template_version: str | None = None,
        config_version: str = "1",
        configuration: dict[str, Any] | None = None,
    ) -> ApplicationInstance:
        context = self._context(principal, workspace_id, project_id)
        self.permissions.require(principal, Permission.APPLICATION_MANAGE, context=context)

        template: ApplicationTemplate | None = None
        if template_id:
            template = self.catalog.get(template_id, template_version)
            if template is None:
                raise KeyError("application_template_not_found")

        requested_type = str(application_type or "").strip()
        if template is not None:
            if requested_type and requested_type != template.application_type:
                raise ValueError("application_type conflicts with selected template")
            kind = template.application_type
            resolved_template_id = template.template_id
            resolved_template_version = template.version
            merged = template.defaults()
        else:
            kind = _clean_token(requested_type, "application_type")
            resolved_template_id = None
            resolved_template_version = None
            merged = {}

        supplied = configuration or {}
        if not isinstance(supplied, dict):
            raise ValueError("configuration must be an object")
        merged.update(json.loads(_json(supplied)))
        merged.setdefault("components", list(template.components) if template else [])

        return self.store.save(
            project_id=project_id,
            application_type=kind,
            template_id=resolved_template_id,
            template_version=resolved_template_version,
            config_version=config_version,
            configuration=merged,
            actor_user_id=principal.user_id,
        )
