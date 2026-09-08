from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

from nutev.tenancy import AuthorizationContext, Permission, PermissionService, Principal, require_opaque_id

DEFAULT_CONFIG_RELATIVE = Path("config/nutev/applications/willian_doctorate_a2_integrative_v1.json")
A2_WORKFLOW_SCHEMA_VERSION = 1
_REQUIRED_GUARDRAILS = (
    "private_by_default",
    "no_inference_from_historical_workstream_name",
    "no_inference_from_query_text",
    "no_inference_from_search_id",
    "no_inference_from_current_user",
    "no_legacy_copy_before_binding",
    "no_search_execution_during_binding",
    "no_result_recalculation_during_binding",
    "no_cross_project_merge",
    "no_article1_import",
    "no_registry_identity_rewrite",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _digest(value: str) -> str:
    return sha256(str(value).encode("utf-8")).hexdigest()


def _require_sha256(value: str, field: str) -> str:
    clean = str(value or "").strip().lower()
    if len(clean) != 64 or any(char not in "0123456789abcdef" for char in clean):
        raise A2ConfigurationError(f"{field} must be a SHA-256 hex digest")
    return clean


def _new_workflow_id() -> str:
    return "i2w_" + uuid4().hex


def _require_workflow_id(value: str) -> str:
    text = str(value or "")
    if not text.startswith("i2w_") or len(text) != 36:
        raise ValueError("invalid article2 workflow_id")
    if any(char not in "0123456789abcdef" for char in text[4:]):
        raise ValueError("invalid article2 workflow_id")
    return text


class A2ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class A2Config:
    assembly_id: str
    config_version: str
    application_template: str
    workflow_type: str
    definition_version: str
    phases: tuple[str, ...]
    legacy_binding_required: bool
    legacy_target_key: str
    legacy_classification: str
    legacy_initial_state: str
    guardrails: dict[str, bool]

    def __post_init__(self) -> None:
        if self.assembly_id != "WILLIAN_DOCTORATE_A2":
            raise A2ConfigurationError("unexpected Article 2 assembly_id")
        if not self.config_version.strip():
            raise A2ConfigurationError("Article 2 config_version is required")
        if self.application_template != "INTEGRATIVE_REVIEW" or self.workflow_type != "INTEGRATIVE_REVIEW":
            raise A2ConfigurationError("Article 2 requires INTEGRATIVE_REVIEW")
        if not self.definition_version.strip():
            raise A2ConfigurationError("workflow definition_version is required")
        if len(self.phases) < 2 or len(self.phases) != len(set(self.phases)) or any(not item for item in self.phases):
            raise A2ConfigurationError("workflow phases must be unique and non-empty")
        if self.phases[0] != "LEGACY_BINDING" or self.phases[-1] != "COMPLETE":
            raise A2ConfigurationError("workflow must start at LEGACY_BINDING and end at COMPLETE")
        if self.legacy_binding_required is not True:
            raise A2ConfigurationError("Article 2 legacy binding must remain required")
        if self.legacy_target_key != "article2_project":
            raise A2ConfigurationError("Article 2 legacy target must be article2_project")
        if self.legacy_classification != "ARTICLE2_PRIVATE":
            raise A2ConfigurationError("Article 2 legacy classification must be ARTICLE2_PRIVATE")
        if self.legacy_initial_state != "REQUIRED_UNMATERIALIZED":
            raise A2ConfigurationError("Article 2 initial binding state must be REQUIRED_UNMATERIALIZED")
        missing = [key for key in _REQUIRED_GUARDRAILS if self.guardrails.get(key) is not True]
        if missing:
            raise A2ConfigurationError("Article 2 guardrails must all be true: " + ", ".join(missing))


@dataclass(frozen=True, slots=True)
class LegacyBindingEvidence:
    """Reviewed migration evidence. No path, query text or search ID is accepted."""

    manifest_sha256: str
    target_key: str
    classification: str
    record_count: int
    source_fingerprints: tuple[str, ...]
    evidence: str
    validation_status: str = "VALIDATED"

    def __post_init__(self) -> None:
        _require_sha256(self.manifest_sha256, "manifest_sha256")
        if self.target_key != "article2_project":
            raise A2ConfigurationError("legacy binding target must be article2_project")
        if self.classification != "ARTICLE2_PRIVATE":
            raise A2ConfigurationError("legacy binding classification must be ARTICLE2_PRIVATE")
        if self.record_count <= 0:
            raise A2ConfigurationError("legacy binding record_count must be positive")
        normalized = tuple(_require_sha256(item, "source_fingerprint") for item in self.source_fingerprints)
        if not normalized or len(normalized) != len(set(normalized)):
            raise A2ConfigurationError("legacy binding requires unique source fingerprints")
        if not self.evidence.strip():
            raise A2ConfigurationError("legacy binding requires reviewed evidence")
        if self.validation_status != "VALIDATED":
            raise A2ConfigurationError("legacy binding must be explicitly VALIDATED")

    def fingerprint(self) -> str:
        payload = {
            "manifest_sha256": self.manifest_sha256.lower(),
            "target_key": self.target_key,
            "classification": self.classification,
            "record_count": self.record_count,
            "source_fingerprints": sorted(item.lower() for item in self.source_fingerprints),
            "evidence_sha256": _digest(self.evidence.strip()),
            "validation_status": self.validation_status,
        }
        return _digest(json.dumps(payload, sort_keys=True, separators=(",", ":")))


@dataclass(frozen=True, slots=True)
class A2WorkflowState:
    workflow_id: str
    workspace_id: str
    project_id: str
    application_id: str
    config_version: str
    current_phase: str
    workflow_status: str
    legacy_binding_state: str
    legacy_binding_fingerprint: str | None
    created_at: datetime
    updated_at: datetime

    @property
    def blocked(self) -> bool:
        return self.workflow_status == "BLOCKED"


def load_a2_config(repo_root: Path, config_path: Path | None = None) -> A2Config:
    root = Path(repo_root).expanduser().resolve()
    path = Path(config_path).expanduser().resolve() if config_path is not None else (root / DEFAULT_CONFIG_RELATIVE).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise A2ConfigurationError("Article 2 config must stay inside repository root") from exc
    if path.is_symlink() or not path.is_file():
        raise A2ConfigurationError("Article 2 config is unavailable")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise A2ConfigurationError("invalid Article 2 config") from exc
    if not isinstance(raw, dict) or int(raw.get("schema_version") or 0) != 1:
        raise A2ConfigurationError("Article 2 config requires schema_version=1")
    if raw.get("record_type") != "NUTEV_APPLICATION_WILLIAN_DOCTORATE_A2_INTEGRATIVE":
        raise A2ConfigurationError("unexpected Article 2 config record_type")
    workflow, binding, guardrails = raw.get("workflow"), raw.get("legacy_binding"), raw.get("guardrails")
    if not all(isinstance(item, dict) for item in (workflow, binding, guardrails)):
        raise A2ConfigurationError("Article 2 workflow/binding/guardrails must be objects")
    phases = workflow.get("phases")
    if not isinstance(phases, list):
        raise A2ConfigurationError("Article 2 phases must be a list")
    return A2Config(
        assembly_id=str(raw.get("assembly_id") or "").strip(),
        config_version=str(raw.get("config_version") or "").strip(),
        application_template=str(raw.get("application_template") or "").strip(),
        workflow_type=str(workflow.get("workflow_type") or "").strip(),
        definition_version=str(workflow.get("definition_version") or "").strip(),
        phases=tuple(str(item).strip() for item in phases),
        legacy_binding_required=binding.get("required") is True,
        legacy_target_key=str(binding.get("target_key") or "").strip(),
        legacy_classification=str(binding.get("required_classification") or "").strip(),
        legacy_initial_state=str(binding.get("initial_state") or "").strip(),
        guardrails={str(key): value is True for key, value in guardrails.items()},
    )


class SQLiteA2WorkflowStore:
    """Private orchestration state only; no query, search ID, document body or filesystem path."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS article2_integrative_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS article2_integrative_workflows (
                workflow_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                application_id TEXT NOT NULL,
                config_version TEXT NOT NULL,
                current_phase TEXT NOT NULL,
                workflow_status TEXT NOT NULL,
                legacy_binding_state TEXT NOT NULL,
                legacy_binding_fingerprint TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(workspace_id, project_id, application_id, config_version)
            );
            CREATE INDEX IF NOT EXISTS idx_article2_integrative_scope
                ON article2_integrative_workflows(workspace_id, project_id, updated_at);
            CREATE TABLE IF NOT EXISTS article2_integrative_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL REFERENCES article2_integrative_workflows(workflow_id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                phase TEXT NOT NULL,
                actor_user_id TEXT NOT NULL,
                evidence_sha256 TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT INTO article2_integrative_meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(A2_WORKFLOW_SCHEMA_VERSION),),
        )
        connection.commit()
        return connection

    @staticmethod
    def _state(row: sqlite3.Row) -> A2WorkflowState:
        return A2WorkflowState(
            workflow_id=str(row["workflow_id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            application_id=str(row["application_id"]),
            config_version=str(row["config_version"]),
            current_phase=str(row["current_phase"]),
            workflow_status=str(row["workflow_status"]),
            legacy_binding_state=str(row["legacy_binding_state"]),
            legacy_binding_fingerprint=str(row["legacy_binding_fingerprint"]) if row["legacy_binding_fingerprint"] else None,
            created_at=_parse_datetime(str(row["created_at"])),
            updated_at=_parse_datetime(str(row["updated_at"])),
        )

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        *,
        workflow_id: str,
        event_type: str,
        phase: str,
        actor_user_id: str,
        evidence_sha256: str | None = None,
    ) -> None:
        connection.execute(
            "INSERT INTO article2_integrative_events(workflow_id,event_type,phase,actor_user_id,evidence_sha256,created_at) VALUES(?,?,?,?,?,?)",
            (workflow_id, event_type, phase, actor_user_id, evidence_sha256, _iso(_now())),
        )

    def bootstrap(
        self,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str,
        config: A2Config,
        actor_user_id: str,
    ) -> A2WorkflowState:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        require_opaque_id(application_id, "application")
        require_opaque_id(actor_user_id, "user")
        existing = self.find(
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            config_version=config.config_version,
        )
        if existing is not None:
            return existing
        workflow_id, now = _new_workflow_id(), _iso(_now())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO article2_integrative_workflows(
                    workflow_id,workspace_id,project_id,application_id,config_version,current_phase,
                    workflow_status,legacy_binding_state,legacy_binding_fingerprint,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?, ?,NULL,?,?)
                """,
                (
                    workflow_id,
                    workspace_id,
                    project_id,
                    application_id,
                    config.config_version,
                    config.phases[0],
                    "BLOCKED",
                    config.legacy_initial_state,
                    now,
                    now,
                ),
            )
            self._event(
                connection,
                workflow_id=workflow_id,
                event_type="workflow_bootstrapped_blocked",
                phase=config.phases[0],
                actor_user_id=actor_user_id,
            )
            connection.commit()
        return self.get(workflow_id, workspace_id=workspace_id, project_id=project_id)

    def find(self, *, workspace_id: str, project_id: str, application_id: str, config_version: str) -> A2WorkflowState | None:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        require_opaque_id(application_id, "application")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM article2_integrative_workflows WHERE workspace_id=? AND project_id=? AND application_id=? AND config_version=?",
                (workspace_id, project_id, application_id, config_version),
            ).fetchone()
        return self._state(row) if row is not None else None

    def get(self, workflow_id: str, *, workspace_id: str, project_id: str) -> A2WorkflowState:
        _require_workflow_id(workflow_id)
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM article2_integrative_workflows WHERE workflow_id=? AND workspace_id=? AND project_id=?",
                (workflow_id, workspace_id, project_id),
            ).fetchone()
        if row is None:
            raise FileNotFoundError(workflow_id)
        return self._state(row)

    def register_binding(
        self,
        *,
        state: A2WorkflowState,
        config: A2Config,
        binding_fingerprint: str,
        actor_user_id: str,
    ) -> A2WorkflowState:
        require_opaque_id(actor_user_id, "user")
        _require_sha256(binding_fingerprint, "binding_fingerprint")
        if not state.blocked or state.current_phase != "LEGACY_BINDING":
            raise ValueError("Article 2 workflow is not waiting for legacy binding")
        next_phase, now = config.phases[1], _iso(_now())
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE article2_integrative_workflows
                SET current_phase=?, workflow_status='ACTIVE', legacy_binding_state='READY',
                    legacy_binding_fingerprint=?, updated_at=?
                WHERE workflow_id=? AND workspace_id=? AND project_id=?
                  AND current_phase='LEGACY_BINDING' AND workflow_status='BLOCKED'
                """,
                (next_phase, binding_fingerprint, now, state.workflow_id, state.workspace_id, state.project_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Article 2 legacy binding transition failed")
            self._event(
                connection,
                workflow_id=state.workflow_id,
                event_type="legacy_binding_validated",
                phase=next_phase,
                actor_user_id=actor_user_id,
                evidence_sha256=binding_fingerprint,
            )
            connection.commit()
        return self.get(state.workflow_id, workspace_id=state.workspace_id, project_id=state.project_id)

    def advance(
        self,
        *,
        state: A2WorkflowState,
        config: A2Config,
        next_phase: str,
        evidence_sha256: str,
        actor_user_id: str,
    ) -> A2WorkflowState:
        require_opaque_id(actor_user_id, "user")
        _require_sha256(evidence_sha256, "phase evidence")
        if state.workflow_status != "ACTIVE":
            raise ValueError("Article 2 workflow is not active")
        try:
            index = config.phases.index(state.current_phase)
        except ValueError as exc:
            raise A2ConfigurationError("stored phase is outside configured Article 2 workflow") from exc
        expected = config.phases[index + 1] if index + 1 < len(config.phases) else None
        if expected is None or next_phase != expected:
            raise ValueError(f"Article 2 next phase must be {expected or 'none'}")
        new_status, now = ("COMPLETE" if next_phase == "COMPLETE" else "ACTIVE"), _iso(_now())
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE article2_integrative_workflows
                SET current_phase=?, workflow_status=?, updated_at=?
                WHERE workflow_id=? AND workspace_id=? AND project_id=?
                  AND current_phase=? AND workflow_status='ACTIVE'
                """,
                (next_phase, new_status, now, state.workflow_id, state.workspace_id, state.project_id, state.current_phase),
            )
            if cursor.rowcount != 1:
                raise ValueError("Article 2 phase transition failed")
            self._event(
                connection,
                workflow_id=state.workflow_id,
                event_type="phase_advanced",
                phase=next_phase,
                actor_user_id=actor_user_id,
                evidence_sha256=evidence_sha256,
            )
            connection.commit()
        return self.get(state.workflow_id, workspace_id=state.workspace_id, project_id=state.project_id)

    def events(self, state: A2WorkflowState) -> tuple[dict[str, Any], ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id,event_type,phase,actor_user_id,evidence_sha256,created_at FROM article2_integrative_events WHERE workflow_id=? ORDER BY id",
                (state.workflow_id,),
            ).fetchall()
        return tuple(
            {
                "id": int(row["id"]),
                "event_type": str(row["event_type"]),
                "phase": str(row["phase"]),
                "actor_user_id": str(row["actor_user_id"]),
                "evidence_sha256": str(row["evidence_sha256"]) if row["evidence_sha256"] else None,
                "created_at": str(row["created_at"]),
            }
            for row in rows
        )


class A2IntegrativeService:
    """A2 workflow orchestration only; generic scientific operations remain separate services."""

    def __init__(
        self,
        *,
        repo_root: Path,
        database_path: Path,
        config_path: Path | None = None,
        permission_service: PermissionService | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).expanduser().resolve()
        self.config_path = Path(config_path).expanduser().resolve() if config_path is not None else None
        self.store = SQLiteA2WorkflowStore(database_path)
        self.permissions = permission_service or PermissionService()

    def config(self) -> A2Config:
        return load_a2_config(self.repo_root, self.config_path)

    @staticmethod
    def _context(workspace_id: str, project_id: str, confirmed: bool) -> AuthorizationContext:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        return AuthorizationContext(workspace_id=workspace_id, project_id=project_id, project_access_confirmed=confirmed)

    def _state(self, *, workspace_id: str, project_id: str, application_id: str) -> A2WorkflowState:
        state = self.store.find(
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            config_version=self.config().config_version,
        )
        if state is None:
            raise FileNotFoundError("Article 2 integrative workflow not bootstrapped")
        return state

    def bootstrap(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str,
        project_access_confirmed: bool,
    ) -> A2WorkflowState:
        context = self._context(workspace_id, project_id, project_access_confirmed)
        self.permissions.require(principal, Permission.APPLICATION_MANAGE, context=context)
        return self.store.bootstrap(
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            config=self.config(),
            actor_user_id=principal.user_id,
        )

    def status(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str,
        project_access_confirmed: bool,
    ) -> dict[str, Any]:
        context = self._context(workspace_id, project_id, project_access_confirmed)
        self.permissions.require(principal, Permission.APPLICATION_READ, context=context)
        config, state = self.config(), self._state(workspace_id=workspace_id, project_id=project_id, application_id=application_id)
        try:
            index = config.phases.index(state.current_phase)
        except ValueError as exc:
            raise A2ConfigurationError("stored phase is outside configured Article 2 workflow") from exc
        next_phase = config.phases[index + 1] if index + 1 < len(config.phases) else None
        return {
            "workflow_id": state.workflow_id,
            "assembly_id": config.assembly_id,
            "config_version": state.config_version,
            "application_id": state.application_id,
            "workflow_type": config.workflow_type,
            "current_phase": state.current_phase,
            "next_phase": next_phase,
            "workflow_status": state.workflow_status,
            "legacy_binding_state": state.legacy_binding_state,
            "legacy_binding_fingerprint": state.legacy_binding_fingerprint,
            "can_advance": state.workflow_status == "ACTIVE" and next_phase is not None,
            "blocked_reason": "LEGACY_BINDING_REQUIRED" if state.legacy_binding_state != "READY" else None,
            "scientific_side_effects": {
                "search_executed": False,
                "results_recomputed": False,
                "registry_identity_rewritten": False,
                "article1_state_imported": False,
                "legacy_files_copied": False,
                "screening_changed": False,
                "extraction_changed": False,
                "synthesis_changed": False,
            },
        }

    def register_legacy_binding(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str,
        project_access_confirmed: bool,
        evidence: LegacyBindingEvidence,
    ) -> A2WorkflowState:
        """Internal migration hook. PR-10 deliberately exposes no HTTP endpoint for it."""
        context = self._context(workspace_id, project_id, project_access_confirmed)
        self.permissions.require(principal, Permission.APPLICATION_MANAGE, context=context)
        config = self.config()
        if evidence.target_key != config.legacy_target_key or evidence.classification != config.legacy_classification:
            raise A2ConfigurationError("legacy binding evidence does not match Article 2 target contract")
        return self.store.register_binding(
            state=self._state(workspace_id=workspace_id, project_id=project_id, application_id=application_id),
            config=config,
            binding_fingerprint=evidence.fingerprint(),
            actor_user_id=principal.user_id,
        )

    def advance(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str,
        project_access_confirmed: bool,
        next_phase: str,
        evidence: str,
    ) -> A2WorkflowState:
        context = self._context(workspace_id, project_id, project_access_confirmed)
        self.permissions.require(principal, Permission.APPLICATION_MANAGE, context=context)
        clean_evidence = str(evidence or "").strip()
        if not clean_evidence:
            raise ValueError("Article 2 phase transition requires evidence")
        state = self._state(workspace_id=workspace_id, project_id=project_id, application_id=application_id)
        if state.legacy_binding_state != "READY":
            raise ValueError("LEGACY_BINDING_REQUIRED")
        return self.store.advance(
            state=state,
            config=self.config(),
            next_phase=str(next_phase or "").strip(),
            evidence_sha256=_digest(clean_evidence),
            actor_user_id=principal.user_id,
        )

    def events(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str,
        project_access_confirmed: bool,
    ) -> tuple[dict[str, Any], ...]:
        context = self._context(workspace_id, project_id, project_access_confirmed)
        self.permissions.require(principal, Permission.APPLICATION_READ, context=context)
        return self.store.events(self._state(workspace_id=workspace_id, project_id=project_id, application_id=application_id))
