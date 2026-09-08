from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
import secrets
import sqlite3
from typing import Any, Iterable
from uuid import uuid4

from nutev.tenancy import (
    AuthorizationContext,
    Permission,
    PermissionDenied,
    PermissionService,
    Principal,
    require_opaque_id,
)

HUMAN_REVIEW_SCHEMA_VERSION = 1
DEFAULT_GUEST_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60
MAX_GUEST_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _token_digest(token: str) -> str:
    return sha256(str(token or "").encode("utf-8")).hexdigest()


_REVIEW_ID_PREFIX = {
    "round": "rnd",
    "reviewer": "rvw",
    "assignment": "asn",
    "decision": "dcs",
    "adjudication": "adj",
}


def _new_id(kind: str) -> str:
    try:
        prefix = _REVIEW_ID_PREFIX[kind]
    except KeyError as exc:
        raise ValueError(f"unsupported review id kind: {kind}") from exc
    return f"{prefix}_{uuid4().hex}"


def _require_review_id(value: str, kind: str) -> str:
    expected = _REVIEW_ID_PREFIX.get(kind)
    text = str(value or "")
    if expected is None or not text.startswith(f"{expected}_") or len(text) != 36:
        raise ValueError(f"invalid {kind}_id")
    suffix = text[4:]
    if any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"invalid {kind}_id")
    return text


class ReviewError(RuntimeError):
    pass


class ReviewAccessDenied(PermissionDenied):
    pass


class ReviewRoundStatus(StrEnum):
    ASSESSMENT = "assessment"
    READY_FOR_ADJUDICATION = "ready_for_adjudication"
    ADJUDICATING = "adjudicating"
    COMPLETE = "complete"


class ReviewerKind(StrEnum):
    USER = "user"
    GUEST = "guest"


@dataclass(frozen=True, slots=True)
class ReviewPolicy:
    decision_options: tuple[str, ...] = ()
    reason_required: bool = True
    minimum_reviewers_per_item: int = 2

    def __post_init__(self) -> None:
        options = tuple(str(item).strip() for item in self.decision_options)
        if any(not item for item in options):
            raise ValueError("decision options cannot be blank")
        if len(options) != len(set(options)):
            raise ValueError("decision options must be unique")
        if self.minimum_reviewers_per_item < 1:
            raise ValueError("minimum_reviewers_per_item must be >= 1")


@dataclass(frozen=True, slots=True)
class ReviewRound:
    id: str
    workspace_id: str
    project_id: str
    name: str
    created_by: str
    status: ReviewRoundStatus
    policy: ReviewPolicy
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewReviewer:
    id: str
    round_id: str
    kind: ReviewerKind
    label: str
    user_id: str | None
    submitted_at: datetime | None
    locked_at: datetime | None
    revoked_at: datetime | None
    token_expires_at: datetime | None
    created_at: datetime

    @property
    def locked(self) -> bool:
        return self.locked_at is not None


@dataclass(frozen=True, slots=True)
class ReviewAssignment:
    id: str
    round_id: str
    reviewer_id: str
    item_key: str
    payload: dict[str, Any]
    allowed_fields: frozenset[str]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    id: str
    round_id: str
    reviewer_id: str
    assignment_id: str
    decision_value: str
    reason: str
    notes: str
    decided_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class GuestReviewPrincipal:
    workspace_id: str
    project_id: str
    round_id: str
    reviewer_id: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewerAccess:
    workspace_id: str
    project_id: str
    round_id: str
    reviewer_id: str
    user_id: str | None = None
    guest: bool = False


@dataclass(frozen=True, slots=True)
class IssuedGuestReviewToken:
    reviewer: ReviewReviewer
    token: str
    principal: GuestReviewPrincipal


@dataclass(frozen=True, slots=True)
class AdjudicationConflict:
    item_key: str
    judgments: tuple[dict[str, str], ...]
    adjudication: dict[str, str] | None = None


class SQLiteHumanReviewStore:
    """Private, tenant-scoped persistence for reusable human review rounds.

    Raw guest tokens are never stored. Only SHA-256 token digests are persisted.
    Scientific source systems remain separate; assignments contain only the payload
    intentionally supplied to this private review round.
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
            CREATE TABLE IF NOT EXISTS human_review_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS human_review_rounds (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_by TEXT NOT NULL,
                status TEXT NOT NULL,
                policy_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_human_review_round_scope
                ON human_review_rounds(workspace_id, project_id, created_at);

            CREATE TABLE IF NOT EXISTS human_review_reviewers (
                id TEXT PRIMARY KEY,
                round_id TEXT NOT NULL REFERENCES human_review_rounds(id) ON DELETE CASCADE,
                reviewer_kind TEXT NOT NULL,
                label TEXT NOT NULL,
                user_id TEXT,
                token_hash TEXT UNIQUE,
                token_expires_at TEXT,
                token_revoked_at TEXT,
                submitted_at TEXT,
                locked_at TEXT,
                created_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_human_review_user_per_round
                ON human_review_reviewers(round_id, user_id)
                WHERE user_id IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_human_review_guest_token
                ON human_review_reviewers(token_hash)
                WHERE token_hash IS NOT NULL;

            CREATE TABLE IF NOT EXISTS human_review_assignments (
                id TEXT PRIMARY KEY,
                round_id TEXT NOT NULL REFERENCES human_review_rounds(id) ON DELETE CASCADE,
                reviewer_id TEXT NOT NULL REFERENCES human_review_reviewers(id) ON DELETE CASCADE,
                item_key TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                allowed_fields_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(round_id, reviewer_id, item_key)
            );
            CREATE INDEX IF NOT EXISTS idx_human_review_assignment_item
                ON human_review_assignments(round_id, item_key);

            CREATE TABLE IF NOT EXISTS human_review_decisions (
                id TEXT PRIMARY KEY,
                round_id TEXT NOT NULL REFERENCES human_review_rounds(id) ON DELETE CASCADE,
                reviewer_id TEXT NOT NULL REFERENCES human_review_reviewers(id) ON DELETE CASCADE,
                assignment_id TEXT NOT NULL UNIQUE REFERENCES human_review_assignments(id) ON DELETE CASCADE,
                decision_value TEXT NOT NULL,
                reason TEXT NOT NULL,
                notes TEXT NOT NULL,
                decided_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS human_review_adjudications (
                id TEXT PRIMARY KEY,
                round_id TEXT NOT NULL REFERENCES human_review_rounds(id) ON DELETE CASCADE,
                item_key TEXT NOT NULL,
                decision_value TEXT NOT NULL,
                adjudicator_user_id TEXT NOT NULL,
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(round_id, item_key)
            );

            CREATE TABLE IF NOT EXISTS human_review_audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id TEXT NOT NULL REFERENCES human_review_rounds(id) ON DELETE CASCADE,
                reviewer_id TEXT,
                actor_user_id TEXT,
                event_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                details_json TEXT NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT INTO human_review_meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(HUMAN_REVIEW_SCHEMA_VERSION),),
        )
        connection.commit()

    @staticmethod
    def _policy_json(policy: ReviewPolicy) -> str:
        return json.dumps(
            {
                "decision_options": list(policy.decision_options),
                "reason_required": policy.reason_required,
                "minimum_reviewers_per_item": policy.minimum_reviewers_per_item,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _policy_from_json(value: str) -> ReviewPolicy:
        payload = json.loads(value)
        if not isinstance(payload, dict):
            raise ReviewError("invalid review policy")
        return ReviewPolicy(
            decision_options=tuple(str(item) for item in payload.get("decision_options") or ()),
            reason_required=bool(payload.get("reason_required", True)),
            minimum_reviewers_per_item=int(payload.get("minimum_reviewers_per_item") or 1),
        )

    @classmethod
    def _round_from_row(cls, row: sqlite3.Row) -> ReviewRound:
        return ReviewRound(
            id=str(row["id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            name=str(row["name"]),
            created_by=str(row["created_by"]),
            status=ReviewRoundStatus(str(row["status"])),
            policy=cls._policy_from_json(str(row["policy_json"])),
            created_at=_parse_datetime(str(row["created_at"])) or _now(),
            updated_at=_parse_datetime(str(row["updated_at"])) or _now(),
        )

    @staticmethod
    def _reviewer_from_row(row: sqlite3.Row) -> ReviewReviewer:
        return ReviewReviewer(
            id=str(row["id"]),
            round_id=str(row["round_id"]),
            kind=ReviewerKind(str(row["reviewer_kind"])),
            label=str(row["label"]),
            user_id=str(row["user_id"]) if row["user_id"] is not None else None,
            submitted_at=_parse_datetime(row["submitted_at"]),
            locked_at=_parse_datetime(row["locked_at"]),
            revoked_at=_parse_datetime(row["token_revoked_at"]),
            token_expires_at=_parse_datetime(row["token_expires_at"]),
            created_at=_parse_datetime(str(row["created_at"])) or _now(),
        )

    @staticmethod
    def _assignment_from_row(row: sqlite3.Row) -> ReviewAssignment:
        payload = json.loads(str(row["payload_json"]))
        allowed = json.loads(str(row["allowed_fields_json"]))
        if not isinstance(payload, dict) or not isinstance(allowed, list):
            raise ReviewError("invalid assignment payload")
        return ReviewAssignment(
            id=str(row["id"]),
            round_id=str(row["round_id"]),
            reviewer_id=str(row["reviewer_id"]),
            item_key=str(row["item_key"]),
            payload=payload,
            allowed_fields=frozenset(str(item) for item in allowed),
            created_at=_parse_datetime(str(row["created_at"])) or _now(),
        )

    @staticmethod
    def _decision_from_row(row: sqlite3.Row) -> ReviewDecision:
        return ReviewDecision(
            id=str(row["id"]),
            round_id=str(row["round_id"]),
            reviewer_id=str(row["reviewer_id"]),
            assignment_id=str(row["assignment_id"]),
            decision_value=str(row["decision_value"]),
            reason=str(row["reason"]),
            notes=str(row["notes"]),
            decided_at=_parse_datetime(str(row["decided_at"])) or _now(),
            updated_at=_parse_datetime(str(row["updated_at"])) or _now(),
        )

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        round_id: str,
        event_type: str,
        *,
        reviewer_id: str | None = None,
        actor_user_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO human_review_audit_events(
                round_id, reviewer_id, actor_user_id, event_type, created_at, details_json
            ) VALUES(?,?,?,?,?,?)
            """,
            (
                round_id,
                reviewer_id,
                actor_user_id,
                event_type,
                _iso(_now()),
                json.dumps(details or {}, sort_keys=True, separators=(",", ":")),
            ),
        )

    def create_round(
        self,
        *,
        workspace_id: str,
        project_id: str,
        name: str,
        created_by: str,
        policy: ReviewPolicy,
    ) -> ReviewRound:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        require_opaque_id(created_by, "user")
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("review round name is required")
        round_id = _new_id("round")
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO human_review_rounds(
                    id, workspace_id, project_id, name, created_by, status,
                    policy_json, created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    round_id,
                    workspace_id,
                    project_id,
                    clean_name,
                    created_by,
                    ReviewRoundStatus.ASSESSMENT.value,
                    self._policy_json(policy),
                    _iso(now),
                    _iso(now),
                ),
            )
            self._audit(connection, round_id, "round_created", actor_user_id=created_by)
            connection.commit()
        return self.get_round(round_id)

    def get_round(self, round_id: str) -> ReviewRound:
        _require_review_id(round_id, "round")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM human_review_rounds WHERE id = ?",
                (round_id,),
            ).fetchone()
        if row is None:
            raise FileNotFoundError(round_id)
        return self._round_from_row(row)

    def list_reviewers(self, round_id: str) -> tuple[ReviewReviewer, ...]:
        _require_review_id(round_id, "round")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM human_review_reviewers WHERE round_id = ? ORDER BY created_at, id",
                (round_id,),
            ).fetchall()
        return tuple(self._reviewer_from_row(row) for row in rows)

    def get_reviewer(self, reviewer_id: str) -> ReviewReviewer:
        _require_review_id(reviewer_id, "reviewer")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM human_review_reviewers WHERE id = ?",
                (reviewer_id,),
            ).fetchone()
        if row is None:
            raise FileNotFoundError(reviewer_id)
        return self._reviewer_from_row(row)

    def reviewer_for_user(self, round_id: str, user_id: str) -> ReviewReviewer | None:
        _require_review_id(round_id, "round")
        require_opaque_id(user_id, "user")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM human_review_reviewers WHERE round_id = ? AND user_id = ?",
                (round_id, user_id),
            ).fetchone()
        return self._reviewer_from_row(row) if row is not None else None

    def add_user_reviewer(self, *, round_id: str, user_id: str, label: str) -> ReviewReviewer:
        _require_review_id(round_id, "round")
        require_opaque_id(user_id, "user")
        clean_label = str(label or "").strip() or user_id
        reviewer_id = _new_id("reviewer")
        now = _now()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO human_review_reviewers(
                        id, round_id, reviewer_kind, label, user_id, token_hash,
                        token_expires_at, token_revoked_at, submitted_at, locked_at, created_at
                    ) VALUES(?,?,?,?,?,NULL,NULL,NULL,NULL,NULL,?)
                    """,
                    (
                        reviewer_id,
                        round_id,
                        ReviewerKind.USER.value,
                        clean_label,
                        user_id,
                        _iso(now),
                    ),
                )
                self._audit(
                    connection,
                    round_id,
                    "reviewer_added",
                    reviewer_id=reviewer_id,
                    details={"kind": ReviewerKind.USER.value},
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("reviewer already exists in round") from exc
        return self.get_reviewer(reviewer_id)

    def issue_guest_reviewer(
        self,
        *,
        round_id: str,
        label: str,
        ttl_seconds: int = DEFAULT_GUEST_TOKEN_TTL_SECONDS,
    ) -> tuple[ReviewReviewer, str]:
        _require_review_id(round_id, "round")
        if ttl_seconds <= 0 or ttl_seconds > MAX_GUEST_TOKEN_TTL_SECONDS:
            raise ValueError("invalid guest token ttl")
        clean_label = str(label or "").strip()
        if not clean_label:
            raise ValueError("guest reviewer label is required")
        reviewer_id = _new_id("reviewer")
        token = secrets.token_urlsafe(32)
        now = _now()
        expires_at = now + timedelta(seconds=ttl_seconds)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO human_review_reviewers(
                    id, round_id, reviewer_kind, label, user_id, token_hash,
                    token_expires_at, token_revoked_at, submitted_at, locked_at, created_at
                ) VALUES(?,?,?,?,NULL,?,?,NULL,NULL,NULL,?)
                """,
                (
                    reviewer_id,
                    round_id,
                    ReviewerKind.GUEST.value,
                    clean_label,
                    _token_digest(token),
                    _iso(expires_at),
                    _iso(now),
                ),
            )
            self._audit(
                connection,
                round_id,
                "guest_reviewer_issued",
                reviewer_id=reviewer_id,
                details={"expires_at": _iso(expires_at)},
            )
            connection.commit()
        return self.get_reviewer(reviewer_id), token

    def resolve_guest_token(self, token: str) -> ReviewReviewer:
        if len(str(token or "")) < 32:
            raise ReviewAccessDenied("invalid guest review token")
        digest = _token_digest(token)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM human_review_reviewers WHERE token_hash = ? AND reviewer_kind = ?",
                (digest, ReviewerKind.GUEST.value),
            ).fetchone()
        if row is None:
            raise ReviewAccessDenied("invalid guest review token")
        reviewer = self._reviewer_from_row(row)
        if reviewer.revoked_at is not None:
            raise ReviewAccessDenied("guest review token revoked")
        if reviewer.token_expires_at is None or reviewer.token_expires_at <= _now():
            raise ReviewAccessDenied("guest review token expired")
        return reviewer

    def revoke_guest(self, reviewer_id: str, *, actor_user_id: str) -> ReviewReviewer:
        reviewer = self.get_reviewer(reviewer_id)
        require_opaque_id(actor_user_id, "user")
        if reviewer.kind is not ReviewerKind.GUEST:
            raise ValueError("reviewer is not a guest")
        now = _now()
        with self._connect() as connection:
            connection.execute(
                "UPDATE human_review_reviewers SET token_revoked_at = ? WHERE id = ?",
                (_iso(now), reviewer_id),
            )
            self._audit(
                connection,
                reviewer.round_id,
                "guest_reviewer_revoked",
                reviewer_id=reviewer_id,
                actor_user_id=actor_user_id,
            )
            connection.commit()
        return self.get_reviewer(reviewer_id)

    def assign_item(
        self,
        *,
        round_id: str,
        reviewer_id: str,
        item_key: str,
        payload: dict[str, Any],
        allowed_fields: Iterable[str],
    ) -> ReviewAssignment:
        _require_review_id(round_id, "round")
        reviewer = self.get_reviewer(reviewer_id)
        if reviewer.round_id != round_id:
            raise ValueError("reviewer belongs to another round")
        clean_item_key = str(item_key or "").strip()
        if not clean_item_key:
            raise ValueError("item_key is required")
        if not isinstance(payload, dict):
            raise ValueError("assignment payload must be an object")
        allowed = frozenset(str(item).strip() for item in allowed_fields if str(item).strip())
        if not allowed.issubset(payload.keys()):
            raise ValueError("allowed_fields must be present in assignment payload")
        assignment_id = _new_id("assignment")
        now = _now()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO human_review_assignments(
                        id, round_id, reviewer_id, item_key, payload_json,
                        allowed_fields_json, created_at
                    ) VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        assignment_id,
                        round_id,
                        reviewer_id,
                        clean_item_key,
                        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                        json.dumps(sorted(allowed), ensure_ascii=False, separators=(",", ":")),
                        _iso(now),
                    ),
                )
                self._audit(
                    connection,
                    round_id,
                    "assignment_created",
                    reviewer_id=reviewer_id,
                    details={"assignment_id": assignment_id, "item_key": clean_item_key},
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("item already assigned to reviewer") from exc
        return self.get_assignment(assignment_id)

    def get_assignment(self, assignment_id: str) -> ReviewAssignment:
        _require_review_id(assignment_id, "assignment")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM human_review_assignments WHERE id = ?",
                (assignment_id,),
            ).fetchone()
        if row is None:
            raise FileNotFoundError(assignment_id)
        return self._assignment_from_row(row)

    def list_assignments(self, round_id: str, reviewer_id: str) -> tuple[ReviewAssignment, ...]:
        _require_review_id(round_id, "round")
        _require_review_id(reviewer_id, "reviewer")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM human_review_assignments
                WHERE round_id = ? AND reviewer_id = ?
                ORDER BY created_at, id
                """,
                (round_id, reviewer_id),
            ).fetchall()
        return tuple(self._assignment_from_row(row) for row in rows)

    def decision_for_assignment(self, assignment_id: str) -> ReviewDecision | None:
        _require_review_id(assignment_id, "assignment")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM human_review_decisions WHERE assignment_id = ?",
                (assignment_id,),
            ).fetchone()
        return self._decision_from_row(row) if row is not None else None

    def save_decision(
        self,
        *,
        reviewer_id: str,
        assignment_id: str,
        decision_value: str,
        reason: str,
        notes: str,
    ) -> ReviewDecision:
        reviewer = self.get_reviewer(reviewer_id)
        if reviewer.locked:
            raise ValueError("reviewer submission is locked")
        assignment = self.get_assignment(assignment_id)
        if assignment.reviewer_id != reviewer_id or assignment.round_id != reviewer.round_id:
            raise ReviewAccessDenied("assignment does not belong to reviewer")
        round_row = self.get_round(reviewer.round_id)
        value = str(decision_value or "").strip()
        clean_reason = str(reason or "").strip()
        clean_notes = str(notes or "").strip()
        if not value:
            raise ValueError("decision_value is required")
        if round_row.policy.decision_options and value not in round_row.policy.decision_options:
            raise ValueError("decision_value is not allowed by round policy")
        if round_row.policy.reason_required and not clean_reason:
            raise ValueError("decision reason is required")
        now = _now()
        existing = self.decision_for_assignment(assignment_id)
        decision_id = existing.id if existing is not None else _new_id("decision")
        decided_at = existing.decided_at if existing is not None else now
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO human_review_decisions(
                    id, round_id, reviewer_id, assignment_id, decision_value,
                    reason, notes, decided_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(assignment_id) DO UPDATE SET
                    decision_value = excluded.decision_value,
                    reason = excluded.reason,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
                """,
                (
                    decision_id,
                    reviewer.round_id,
                    reviewer_id,
                    assignment_id,
                    value,
                    clean_reason,
                    clean_notes,
                    _iso(decided_at),
                    _iso(now),
                ),
            )
            self._audit(
                connection,
                reviewer.round_id,
                "decision_saved",
                reviewer_id=reviewer_id,
                details={"assignment_id": assignment_id},
            )
            connection.commit()
        result = self.decision_for_assignment(assignment_id)
        if result is None:
            raise ReviewError("decision was not persisted")
        return result

    def submit_reviewer(self, reviewer_id: str) -> ReviewReviewer:
        reviewer = self.get_reviewer(reviewer_id)
        if reviewer.locked:
            return reviewer
        round_row = self.get_round(reviewer.round_id)
        assignments = self.list_assignments(reviewer.round_id, reviewer_id)
        if not assignments:
            raise ValueError("reviewer has no assignments")
        decisions = {item.id: self.decision_for_assignment(item.id) for item in assignments}
        missing = [assignment.id for assignment in assignments if decisions[assignment.id] is None]
        if missing:
            raise ValueError(f"complete all assignments before submit ({len(assignments) - len(missing)}/{len(assignments)})")
        if round_row.policy.reason_required:
            missing_reason = [
                assignment.id
                for assignment in assignments
                if not str(decisions[assignment.id].reason if decisions[assignment.id] else "").strip()
            ]
            if missing_reason:
                raise ValueError("all decisions require a reason before submit")

        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE human_review_reviewers
                SET submitted_at = ?, locked_at = ?
                WHERE id = ? AND submitted_at IS NULL AND locked_at IS NULL
                """,
                (_iso(now), _iso(now), reviewer_id),
            )
            self._audit(
                connection,
                reviewer.round_id,
                "reviewer_submitted_locked",
                reviewer_id=reviewer_id,
                details={"assignment_count": len(assignments)},
            )
            remaining = connection.execute(
                "SELECT COUNT(*) AS n FROM human_review_reviewers WHERE round_id = ? AND locked_at IS NULL",
                (reviewer.round_id,),
            ).fetchone()
            status = (
                ReviewRoundStatus.READY_FOR_ADJUDICATION
                if int(remaining["n"] or 0) == 0
                else ReviewRoundStatus.ASSESSMENT
            )
            connection.execute(
                "UPDATE human_review_rounds SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, _iso(now), reviewer.round_id),
            )
            connection.commit()
        return self.get_reviewer(reviewer_id)

    def adjudication_snapshot(self, round_id: str) -> dict[str, Any]:
        round_row = self.get_round(round_id)
        reviewers = self.list_reviewers(round_id)
        if not reviewers or any(not reviewer.locked for reviewer in reviewers):
            raise ValueError("all reviewers must submit and lock before adjudication")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT a.item_key, a.reviewer_id, d.decision_value, d.reason
                FROM human_review_assignments a
                LEFT JOIN human_review_decisions d ON d.assignment_id = a.id
                WHERE a.round_id = ?
                ORDER BY a.item_key, a.reviewer_id
                """,
                (round_id,),
            ).fetchall()
            adjudications = connection.execute(
                "SELECT * FROM human_review_adjudications WHERE round_id = ?",
                (round_id,),
            ).fetchall()

        grouped: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            if row["decision_value"] is None:
                raise ReviewError("locked reviewer has assignment without decision")
            grouped.setdefault(str(row["item_key"]), []).append(
                {
                    "reviewer_id": str(row["reviewer_id"]),
                    "decision_value": str(row["decision_value"]),
                    "reason": str(row["reason"] or ""),
                }
            )
        saved = {str(row["item_key"]): row for row in adjudications}
        agreements: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        for item_key, judgments in sorted(grouped.items()):
            reviewer_ids = {item["reviewer_id"] for item in judgments}
            if len(reviewer_ids) < round_row.policy.minimum_reviewers_per_item:
                raise ValueError(
                    f"item {item_key} has {len(reviewer_ids)} reviewer(s); "
                    f"minimum is {round_row.policy.minimum_reviewers_per_item}"
                )
            values = {item["decision_value"] for item in judgments}
            if len(values) == 1:
                agreements.append(
                    {
                        "item_key": item_key,
                        "decision_value": next(iter(values)),
                        "reviewer_count": len(reviewer_ids),
                    }
                )
                continue
            adjudication_row = saved.get(item_key)
            adjudication = None
            if adjudication_row is not None:
                adjudication = {
                    "decision_value": str(adjudication_row["decision_value"]),
                    "adjudicator_user_id": str(adjudication_row["adjudicator_user_id"]),
                    "notes": str(adjudication_row["notes"] or ""),
                    "updated_at": str(adjudication_row["updated_at"]),
                }
            conflicts.append(
                {
                    "item_key": item_key,
                    "judgments": judgments,
                    "adjudication": adjudication,
                }
            )
        return {
            "round_id": round_id,
            "status": round_row.status.value,
            "agreement_count": len(agreements),
            "conflict_count": len(conflicts),
            "resolved_conflicts": sum(1 for item in conflicts if item["adjudication"] is not None),
            "unresolved_conflicts": sum(1 for item in conflicts if item["adjudication"] is None),
            "agreements": agreements,
            "conflicts": conflicts,
        }

    def save_adjudication(
        self,
        *,
        round_id: str,
        item_key: str,
        decision_value: str,
        adjudicator_user_id: str,
        notes: str,
    ) -> dict[str, Any]:
        require_opaque_id(adjudicator_user_id, "user")
        snapshot = self.adjudication_snapshot(round_id)
        conflict = next((item for item in snapshot["conflicts"] if item["item_key"] == item_key), None)
        if conflict is None:
            raise ValueError("item is not an adjudicable conflict")
        round_row = self.get_round(round_id)
        value = str(decision_value or "").strip()
        if not value:
            raise ValueError("adjudication decision is required")
        if round_row.policy.decision_options and value not in round_row.policy.decision_options:
            raise ValueError("adjudication decision is not allowed by round policy")
        now = _now()
        adjudication_id = _new_id("adjudication")
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT id, created_at FROM human_review_adjudications WHERE round_id = ? AND item_key = ?",
                (round_id, item_key),
            ).fetchone()
            if existing is not None:
                adjudication_id = str(existing["id"])
                created_at = str(existing["created_at"])
            else:
                created_at = _iso(now)
            connection.execute(
                """
                INSERT INTO human_review_adjudications(
                    id, round_id, item_key, decision_value, adjudicator_user_id,
                    notes, created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(round_id, item_key) DO UPDATE SET
                    decision_value = excluded.decision_value,
                    adjudicator_user_id = excluded.adjudicator_user_id,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
                """,
                (
                    adjudication_id,
                    round_id,
                    item_key,
                    value,
                    adjudicator_user_id,
                    str(notes or "").strip(),
                    created_at,
                    _iso(now),
                ),
            )
            connection.execute(
                "UPDATE human_review_rounds SET status = ?, updated_at = ? WHERE id = ?",
                (ReviewRoundStatus.ADJUDICATING.value, _iso(now), round_id),
            )
            self._audit(
                connection,
                round_id,
                "conflict_adjudicated",
                actor_user_id=adjudicator_user_id,
                details={"item_key": item_key},
            )
            connection.commit()
        return self.adjudication_snapshot(round_id)

    def finalize_adjudication(self, round_id: str, *, actor_user_id: str) -> dict[str, Any]:
        require_opaque_id(actor_user_id, "user")
        snapshot = self.adjudication_snapshot(round_id)
        if int(snapshot["unresolved_conflicts"]) != 0:
            raise ValueError("unresolved adjudication conflicts remain")
        now = _now()
        with self._connect() as connection:
            connection.execute(
                "UPDATE human_review_rounds SET status = ?, updated_at = ? WHERE id = ?",
                (ReviewRoundStatus.COMPLETE.value, _iso(now), round_id),
            )
            self._audit(
                connection,
                round_id,
                "adjudication_complete",
                actor_user_id=actor_user_id,
                details={"conflict_count": int(snapshot["conflict_count"])},
            )
            connection.commit()
        return self.adjudication_snapshot(round_id)

    def audit_events(self, round_id: str) -> tuple[dict[str, Any], ...]:
        _require_review_id(round_id, "round")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM human_review_audit_events WHERE round_id = ? ORDER BY id",
                (round_id,),
            ).fetchall()
        return tuple(
            {
                "id": int(row["id"]),
                "round_id": str(row["round_id"]),
                "reviewer_id": str(row["reviewer_id"]) if row["reviewer_id"] else None,
                "actor_user_id": str(row["actor_user_id"]) if row["actor_user_id"] else None,
                "event_type": str(row["event_type"]),
                "created_at": str(row["created_at"]),
                "details": json.loads(str(row["details_json"])),
            }
            for row in rows
        )


class HumanReviewEngine:
    """Reusable review orchestration with tenant and assignment isolation.

    The engine is deliberately application-agnostic: it does not know Article 1,
    Article 2, scoping reviews, integrative reviews, D-132, NutEV ranking, or any
    manuscript-specific scientific rule.
    """

    def __init__(
        self,
        store: SQLiteHumanReviewStore,
        *,
        permission_service: PermissionService | None = None,
    ) -> None:
        self.store = store
        self.permissions = permission_service or PermissionService()

    @staticmethod
    def _context(
        workspace_id: str,
        project_id: str,
        *,
        project_access_confirmed: bool,
        assigned: bool = False,
    ) -> AuthorizationContext:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        return AuthorizationContext(
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=project_access_confirmed,
            assigned=assigned,
        )

    def _round_in_scope(self, round_id: str, workspace_id: str, project_id: str) -> ReviewRound:
        round_row = self.store.get_round(round_id)
        if round_row.workspace_id != workspace_id or round_row.project_id != project_id:
            raise FileNotFoundError(round_id)
        return round_row

    def create_round(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        name: str,
        policy: ReviewPolicy | None = None,
    ) -> ReviewRound:
        context = self._context(
            workspace_id,
            project_id,
            project_access_confirmed=project_access_confirmed,
        )
        self.permissions.require(principal, Permission.HUMAN_REVIEW_MANAGE, context=context)
        return self.store.create_round(
            workspace_id=workspace_id,
            project_id=project_id,
            name=name,
            created_by=principal.user_id,
            policy=policy or ReviewPolicy(),
        )

    def round_summary(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
    ) -> dict[str, Any]:
        round_row = self._round_in_scope(round_id, workspace_id, project_id)
        reviewer = self.store.reviewer_for_user(round_id, principal.user_id)
        context = self._context(
            workspace_id,
            project_id,
            project_access_confirmed=project_access_confirmed,
            assigned=reviewer is not None,
        )
        self.permissions.require(principal, Permission.HUMAN_REVIEW_READ, context=context)
        reviewers = self.store.list_reviewers(round_id)
        return {
            "round": {
                "id": round_row.id,
                "workspace_id": round_row.workspace_id,
                "project_id": round_row.project_id,
                "name": round_row.name,
                "status": round_row.status.value,
                "policy": asdict(round_row.policy),
                "created_at": _iso(round_row.created_at),
                "updated_at": _iso(round_row.updated_at),
            },
            "reviewers": [
                {
                    "id": item.id,
                    "kind": item.kind.value,
                    "label": item.label,
                    "submitted": item.submitted_at is not None,
                    "locked": item.locked,
                    "revoked": item.revoked_at is not None,
                }
                for item in reviewers
            ],
        }

    def add_user_reviewer(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
        reviewer_user_id: str,
        label: str,
    ) -> ReviewReviewer:
        self._round_in_scope(round_id, workspace_id, project_id)
        context = self._context(workspace_id, project_id, project_access_confirmed=project_access_confirmed)
        self.permissions.require(principal, Permission.HUMAN_REVIEW_MANAGE, context=context)
        return self.store.add_user_reviewer(
            round_id=round_id,
            user_id=reviewer_user_id,
            label=label,
        )

    def issue_guest_reviewer(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
        label: str,
        ttl_seconds: int = DEFAULT_GUEST_TOKEN_TTL_SECONDS,
    ) -> IssuedGuestReviewToken:
        self._round_in_scope(round_id, workspace_id, project_id)
        context = self._context(workspace_id, project_id, project_access_confirmed=project_access_confirmed)
        self.permissions.require(principal, Permission.HUMAN_REVIEW_MANAGE, context=context)
        reviewer, token = self.store.issue_guest_reviewer(
            round_id=round_id,
            label=label,
            ttl_seconds=ttl_seconds,
        )
        if reviewer.token_expires_at is None:
            raise ReviewError("guest reviewer expiration missing")
        return IssuedGuestReviewToken(
            reviewer=reviewer,
            token=token,
            principal=GuestReviewPrincipal(
                workspace_id=workspace_id,
                project_id=project_id,
                round_id=round_id,
                reviewer_id=reviewer.id,
                expires_at=reviewer.token_expires_at,
            ),
        )

    def revoke_guest_reviewer(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
        reviewer_id: str,
    ) -> ReviewReviewer:
        self._round_in_scope(round_id, workspace_id, project_id)
        reviewer = self.store.get_reviewer(reviewer_id)
        if reviewer.round_id != round_id:
            raise FileNotFoundError(reviewer_id)
        context = self._context(workspace_id, project_id, project_access_confirmed=project_access_confirmed)
        self.permissions.require(principal, Permission.HUMAN_REVIEW_MANAGE, context=context)
        return self.store.revoke_guest(reviewer_id, actor_user_id=principal.user_id)

    def assign_item(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
        reviewer_id: str,
        item_key: str,
        payload: dict[str, Any],
        allowed_fields: Iterable[str],
    ) -> ReviewAssignment:
        self._round_in_scope(round_id, workspace_id, project_id)
        reviewer = self.store.get_reviewer(reviewer_id)
        if reviewer.round_id != round_id:
            raise FileNotFoundError(reviewer_id)
        context = self._context(workspace_id, project_id, project_access_confirmed=project_access_confirmed)
        self.permissions.require(principal, Permission.HUMAN_REVIEW_MANAGE, context=context)
        return self.store.assign_item(
            round_id=round_id,
            reviewer_id=reviewer_id,
            item_key=item_key,
            payload=payload,
            allowed_fields=allowed_fields,
        )

    def access_for_user(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
    ) -> ReviewerAccess:
        self._round_in_scope(round_id, workspace_id, project_id)
        reviewer = self.store.reviewer_for_user(round_id, principal.user_id)
        if reviewer is None:
            raise FileNotFoundError(round_id)
        context = self._context(
            workspace_id,
            project_id,
            project_access_confirmed=project_access_confirmed,
            assigned=True,
        )
        self.permissions.require(principal, Permission.SCREEN, context=context)
        return ReviewerAccess(
            workspace_id=workspace_id,
            project_id=project_id,
            round_id=round_id,
            reviewer_id=reviewer.id,
            user_id=principal.user_id,
            guest=False,
        )

    def access_for_guest(self, token: str) -> ReviewerAccess:
        reviewer = self.store.resolve_guest_token(token)
        round_row = self.store.get_round(reviewer.round_id)
        return ReviewerAccess(
            workspace_id=round_row.workspace_id,
            project_id=round_row.project_id,
            round_id=round_row.id,
            reviewer_id=reviewer.id,
            user_id=None,
            guest=True,
        )

    def review_payload(self, access: ReviewerAccess) -> dict[str, Any]:
        round_row = self._round_in_scope(access.round_id, access.workspace_id, access.project_id)
        reviewer = self.store.get_reviewer(access.reviewer_id)
        if reviewer.round_id != access.round_id:
            raise ReviewAccessDenied("reviewer scope mismatch")
        if access.guest:
            if reviewer.kind is not ReviewerKind.GUEST:
                raise ReviewAccessDenied("reviewer is not guest-scoped")
            if reviewer.revoked_at is not None:
                raise ReviewAccessDenied("guest review token revoked")
            if reviewer.token_expires_at is None or reviewer.token_expires_at <= _now():
                raise ReviewAccessDenied("guest review token expired")
        elif reviewer.user_id != access.user_id:
            raise ReviewAccessDenied("reviewer identity mismatch")

        assignments = self.store.list_assignments(access.round_id, access.reviewer_id)
        items: list[dict[str, Any]] = []
        for assignment in assignments:
            filtered_payload = {
                key: value
                for key, value in assignment.payload.items()
                if key in assignment.allowed_fields
            }
            decision = self.store.decision_for_assignment(assignment.id)
            items.append(
                {
                    "assignment_id": assignment.id,
                    "item_key": assignment.item_key,
                    "payload": filtered_payload,
                    "decision": (
                        {
                            "decision_value": decision.decision_value,
                            "reason": decision.reason,
                            "notes": decision.notes,
                            "updated_at": _iso(decision.updated_at),
                        }
                        if decision is not None
                        else None
                    ),
                }
            )
        completed = sum(1 for item in items if item["decision"] is not None)
        return {
            "round_id": round_row.id,
            "round_name": round_row.name,
            "reviewer_id": reviewer.id,
            "reviewer_label": reviewer.label,
            "locked": reviewer.locked,
            "submitted_at": _iso(reviewer.submitted_at) if reviewer.submitted_at else None,
            "policy": {
                "decision_options": list(round_row.policy.decision_options),
                "reason_required": round_row.policy.reason_required,
            },
            "completed_items": completed,
            "total_items": len(items),
            "assignments": items,
        }

    def save_decision(
        self,
        access: ReviewerAccess,
        *,
        assignment_id: str,
        decision_value: str,
        reason: str,
        notes: str = "",
    ) -> dict[str, Any]:
        self.review_payload(access)
        assignment = self.store.get_assignment(assignment_id)
        if assignment.round_id != access.round_id or assignment.reviewer_id != access.reviewer_id:
            raise FileNotFoundError(assignment_id)
        self.store.save_decision(
            reviewer_id=access.reviewer_id,
            assignment_id=assignment_id,
            decision_value=decision_value,
            reason=reason,
            notes=notes,
        )
        return self.review_payload(access)

    def submit(self, access: ReviewerAccess) -> dict[str, Any]:
        self.review_payload(access)
        self.store.submit_reviewer(access.reviewer_id)
        return self.review_payload(access)

    def adjudication_payload(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
    ) -> dict[str, Any]:
        self._round_in_scope(round_id, workspace_id, project_id)
        context = self._context(workspace_id, project_id, project_access_confirmed=project_access_confirmed)
        self.permissions.require(principal, Permission.ADJUDICATE, context=context)
        return self.store.adjudication_snapshot(round_id)

    def save_adjudication(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
        item_key: str,
        decision_value: str,
        notes: str = "",
    ) -> dict[str, Any]:
        self._round_in_scope(round_id, workspace_id, project_id)
        context = self._context(workspace_id, project_id, project_access_confirmed=project_access_confirmed)
        self.permissions.require(principal, Permission.ADJUDICATE, context=context)
        return self.store.save_adjudication(
            round_id=round_id,
            item_key=item_key,
            decision_value=decision_value,
            adjudicator_user_id=principal.user_id,
            notes=notes,
        )

    def finalize_adjudication(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
    ) -> dict[str, Any]:
        self._round_in_scope(round_id, workspace_id, project_id)
        context = self._context(workspace_id, project_id, project_access_confirmed=project_access_confirmed)
        self.permissions.require(principal, Permission.ADJUDICATE, context=context)
        return self.store.finalize_adjudication(round_id, actor_user_id=principal.user_id)

    def audit_events(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
    ) -> tuple[dict[str, Any], ...]:
        self._round_in_scope(round_id, workspace_id, project_id)
        context = self._context(workspace_id, project_id, project_access_confirmed=project_access_confirmed)
        self.permissions.require(principal, Permission.HUMAN_REVIEW_MANAGE, context=context)
        return self.store.audit_events(round_id)