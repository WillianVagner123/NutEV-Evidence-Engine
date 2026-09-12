from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from nutev.tenancy import (
    ApplicationService,
    AuthorizationContext,
    Permission,
    PermissionDenied,
    PermissionService,
    Principal,
    require_opaque_id,
)

from .engine import HumanReviewEngine, ReviewPolicy

REVIEW_APPLICATION_BINDING_SCHEMA_VERSION = 1


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class ReviewApplicationBinding:
    round_id: str
    workspace_id: str
    project_id: str
    application_id: str
    created_at: datetime


class SQLiteReviewApplicationBindingStore:
    """Application binding for otherwise application-agnostic human review rounds.

    The reusable HumanReviewEngine deliberately remains unaware of research
    application types. This store supplies the hosted-product boundary that makes a
    round visible only inside the explicitly bound ResearchApplication.

    Existing historical/application-specific rounds are intentionally unbound and
    therefore never become generic Review surface content by inference.
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        self._apply_schema(connection)
        return connection

    @staticmethod
    def _apply_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS human_review_application_binding_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS human_review_application_bindings (
                round_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                application_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_human_review_application_scope
                ON human_review_application_bindings(
                    workspace_id, project_id, application_id, created_at
                );
            """
        )
        connection.execute(
            "INSERT INTO human_review_application_binding_meta(key, value) "
            "VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(REVIEW_APPLICATION_BINDING_SCHEMA_VERSION),),
        )
        connection.commit()

    @staticmethod
    def _binding(row: sqlite3.Row) -> ReviewApplicationBinding:
        return ReviewApplicationBinding(
            round_id=str(row["round_id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            application_id=str(row["application_id"]),
            created_at=_parse_datetime(str(row["created_at"])),
        )

    def bind(
        self,
        *,
        round_id: str,
        workspace_id: str,
        project_id: str,
        application_id: str,
    ) -> ReviewApplicationBinding:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        require_opaque_id(application_id, "application")
        clean_round_id = str(round_id or "").strip()
        if not clean_round_id.startswith("rnd_"):
            raise ValueError("invalid round_id")
        now = _now()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM human_review_application_bindings WHERE round_id = ?",
                (clean_round_id,),
            ).fetchone()
            if existing is not None:
                binding = self._binding(existing)
                if (
                    binding.workspace_id != workspace_id
                    or binding.project_id != project_id
                    or binding.application_id != application_id
                ):
                    raise ValueError("review round already bound to another application scope")
                return binding
            connection.execute(
                """
                INSERT INTO human_review_application_bindings(
                    round_id, workspace_id, project_id, application_id, created_at
                ) VALUES(?,?,?,?,?)
                """,
                (clean_round_id, workspace_id, project_id, application_id, _iso(now)),
            )
            connection.commit()
        binding = self.get(clean_round_id)
        if binding is None:
            raise RuntimeError("review application binding disappeared after save")
        return binding

    def get(self, round_id: str) -> ReviewApplicationBinding | None:
        clean_round_id = str(round_id or "").strip()
        if not clean_round_id:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM human_review_application_bindings WHERE round_id = ?",
                (clean_round_id,),
            ).fetchone()
        return self._binding(row) if row is not None else None

    def list_round_ids(
        self,
        *,
        workspace_id: str,
        project_id: str,
        application_id: str,
    ) -> tuple[str, ...]:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        require_opaque_id(application_id, "application")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT round_id
                FROM human_review_application_bindings
                WHERE workspace_id = ? AND project_id = ? AND application_id = ?
                ORDER BY created_at DESC, round_id DESC
                """,
                (workspace_id, project_id, application_id),
            ).fetchall()
        return tuple(str(row["round_id"]) for row in rows)


class ApplicationScopedReviewService:
    """Hosted-product application boundary over the reusable HumanReviewEngine."""

    def __init__(
        self,
        engine: HumanReviewEngine,
        applications: ApplicationService,
        bindings: SQLiteReviewApplicationBindingStore,
        *,
        permissions: PermissionService | None = None,
    ) -> None:
        self.engine = engine
        self.applications = applications
        self.bindings = bindings
        self.permissions = permissions or PermissionService()

    def _application(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
    ):
        application = self.applications.get(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        if application is None:
            raise LookupError("review_application_required")
        return application

    @staticmethod
    def _context(workspace_id: str, project_id: str, *, assigned: bool = False) -> AuthorizationContext:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        return AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            assigned=assigned,
        )

    def _binding_in_current_application(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        round_id: str,
    ) -> ReviewApplicationBinding:
        application = self._application(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        binding = self.bindings.get(round_id)
        if binding is None:
            raise FileNotFoundError(round_id)
        if (
            binding.workspace_id != workspace_id
            or binding.project_id != project_id
            or binding.application_id != application.application.id
        ):
            raise FileNotFoundError(round_id)
        return binding

    @staticmethod
    def _round_descriptor(
        summary: dict[str, Any],
        *,
        application_id: str,
        assigned_to_current_user: bool,
    ) -> dict[str, Any]:
        round_payload = dict(summary.get("round") or {})
        return {
            **round_payload,
            "application_id": application_id,
            "reviewers": list(summary.get("reviewers") or []),
            "assigned_to_current_user": assigned_to_current_user,
        }

    def overview(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        application = self._application(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        application_id = application.application.id
        context = self._context(workspace_id, project_id)
        can_manage = self.permissions.can(
            principal,
            Permission.HUMAN_REVIEW_MANAGE,
            context=context,
        )
        rounds: list[dict[str, Any]] = []
        for round_id in self.bindings.list_round_ids(
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
        ):
            reviewer = self.engine.store.reviewer_for_user(round_id, principal.user_id)
            try:
                summary = self.engine.round_summary(
                    principal,
                    workspace_id=workspace_id,
                    project_id=project_id,
                    project_access_confirmed=True,
                    round_id=round_id,
                )
            except PermissionDenied:
                continue
            rounds.append(
                self._round_descriptor(
                    summary,
                    application_id=application_id,
                    assigned_to_current_user=reviewer is not None,
                )
            )
        return {
            "workspace_id": workspace_id,
            "project_id": project_id,
            "application": application.descriptor(),
            "rounds": rounds,
            "can_manage": can_manage,
            "legacy_unbound_rounds_visible": False,
            "scientific_decisions_automatic": False,
        }

    def create_round(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        name: str,
        policy: ReviewPolicy,
    ) -> dict[str, Any]:
        application = self._application(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        context = self._context(workspace_id, project_id)
        self.permissions.require(
            principal,
            Permission.HUMAN_REVIEW_MANAGE,
            context=context,
        )
        round_row = self.engine.create_round(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            name=name,
            policy=policy,
        )
        binding = self.bindings.bind(
            round_id=round_row.id,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application.application.id,
        )
        summary = self.engine.round_summary(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_row.id,
        )
        return self._round_descriptor(
            summary,
            application_id=binding.application_id,
            assigned_to_current_user=False,
        )

    def round_summary(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        round_id: str,
    ) -> dict[str, Any]:
        binding = self._binding_in_current_application(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            round_id=round_id,
        )
        reviewer = self.engine.store.reviewer_for_user(round_id, principal.user_id)
        summary = self.engine.round_summary(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_id,
        )
        return self._round_descriptor(
            summary,
            application_id=binding.application_id,
            assigned_to_current_user=reviewer is not None,
        )

    def reviewer_payload(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        round_id: str,
    ) -> dict[str, Any]:
        binding = self._binding_in_current_application(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            round_id=round_id,
        )
        access = self.engine.access_for_user(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_id,
        )
        payload = self.engine.review_payload(access)
        return {"application_id": binding.application_id, **payload}

    def save_decision(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        round_id: str,
        assignment_id: str,
        decision_value: str,
        reason: str,
        notes: str = "",
    ) -> dict[str, Any]:
        self._binding_in_current_application(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            round_id=round_id,
        )
        access = self.engine.access_for_user(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_id,
        )
        return self.engine.save_decision(
            access,
            assignment_id=assignment_id,
            decision_value=decision_value,
            reason=reason,
            notes=notes,
        )

    def submit(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        round_id: str,
    ) -> dict[str, Any]:
        self._binding_in_current_application(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            round_id=round_id,
        )
        access = self.engine.access_for_user(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_id,
        )
        return self.engine.submit(access)
