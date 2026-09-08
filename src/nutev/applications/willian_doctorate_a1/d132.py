from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import random
import sqlite3
from typing import Any, Iterable

from nutev.review import HumanReviewEngine, IssuedGuestReviewToken, ReviewPolicy, SQLiteHumanReviewStore
from nutev.tenancy import Principal, require_opaque_id

DEFAULT_CONFIG_RELATIVE = Path("config/nutev/applications/willian_doctorate_a1_d132_v1.json")
D132_SCHEMA_VERSION = 1

_ALLOWED_SAMPLING_MODES = {"MANIFEST_EXACT", "EXPLICIT_RECORD_IDS"}
_REQUIRED_GUARDRAILS = (
    "private_by_default",
    "source_is_read_only",
    "no_resampling_in_manifest_exact_mode",
    "no_automatic_press_pass",
    "no_automatic_c4_decision",
    "no_automatic_gf10_authorization",
    "no_automatic_query_freeze",
    "no_formal_search_execution",
    "no_prisma_creation",
    "no_registry_mutation",
    "no_article_id_rewrite",
)
_FORBIDDEN_REVIEW_FIELDS = {
    "r1_decision",
    "rank",
    "score",
    "nutev_rank",
    "nutev_score",
    "machine_relevance",
    "other_reviewer_decision",
    "reviewer_a_decision",
    "reviewer_b_decision",
    "adjudicated_decision",
}
_HUMAN_LABEL_KEYS = {
    "decision",
    "human_decision",
    "label",
    "decision_y_n_u",
    "reviewer_id",
    "reviewed_at",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _normalized_text_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def _record_ids_sha256(record_ids: Iterable[str]) -> str:
    return _sha256_bytes("\n".join(str(item) for item in record_ids).encode("utf-8"))


def _safe_under(root: Path, candidate: Path, *, label: str) -> Path:
    base = root.expanduser().resolve()
    path = candidate.expanduser().resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise D132ConfigurationError(f"{label} must stay inside repository root") from exc
    if path.is_symlink():
        raise D132ConfigurationError(f"{label} must not be a symlink")
    return path


def _safe_relative_file(root: Path, relative: str, *, label: str) -> Path:
    raw = Path(str(relative or "").strip())
    if not str(raw) or raw.is_absolute() or ".." in raw.parts:
        raise D132ConfigurationError(f"{label} must be a safe repository-relative path")
    path = _safe_under(root, root / raw, label=label)
    if not path.is_file():
        raise D132ConfigurationError(f"{label} not found: {raw.as_posix()}")
    return path


def _json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise D132ConfigurationError(f"invalid {label}") from exc
    if not isinstance(payload, dict):
        raise D132ConfigurationError(f"{label} must be a JSON object")
    return payload


class D132ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class D132Config:
    config_version: str
    protocol_id: str
    application_template: str
    manifest_path: str
    expected_record_type: str
    expected_run_id: str
    expected_source_run_sha256: str
    expected_record_count: int
    sampling_mode: str
    explicit_record_ids: tuple[str, ...]
    decision_options: tuple[str, ...]
    reason_required: bool
    minimum_reviewers_per_item: int
    reviewer_slots: tuple[str, ...]
    guest_token_ttl_seconds: int
    allowed_fields: frozenset[str]
    guardrails: dict[str, bool]

    def __post_init__(self) -> None:
        if not self.config_version.strip():
            raise D132ConfigurationError("config_version is required")
        if self.protocol_id != "D-132":
            raise D132ConfigurationError("protocol_id must be D-132")
        if self.application_template != "SCOPING_REVIEW":
            raise D132ConfigurationError("D-132 requires SCOPING_REVIEW application template")
        if self.expected_record_count <= 0:
            raise D132ConfigurationError("expected_record_count must be positive")
        if self.sampling_mode not in _ALLOWED_SAMPLING_MODES:
            raise D132ConfigurationError("unsupported D-132 sampling mode")
        if self.sampling_mode == "MANIFEST_EXACT" and self.explicit_record_ids:
            raise D132ConfigurationError("MANIFEST_EXACT cannot contain explicit_record_ids")
        if self.sampling_mode == "EXPLICIT_RECORD_IDS" and not self.explicit_record_ids:
            raise D132ConfigurationError("EXPLICIT_RECORD_IDS requires at least one record_id")
        if len(self.explicit_record_ids) != len(set(self.explicit_record_ids)):
            raise D132ConfigurationError("explicit_record_ids must be unique")
        if self.decision_options != ("Y", "N", "U"):
            raise D132ConfigurationError("D-132 decision options must preserve Y/N/U")
        if self.minimum_reviewers_per_item < 2:
            raise D132ConfigurationError("D-132 requires at least two independent reviewers")
        if self.reviewer_slots != ("A", "B"):
            raise D132ConfigurationError("D-132 v1 requires reviewer slots A and B")
        if self.minimum_reviewers_per_item > len(self.reviewer_slots):
            raise D132ConfigurationError("minimum reviewers exceeds configured reviewer slots")
        if self.guest_token_ttl_seconds <= 0:
            raise D132ConfigurationError("guest token ttl must be positive")
        if not self.allowed_fields:
            raise D132ConfigurationError("D-132 allowed_fields cannot be empty")
        forbidden = {item.casefold() for item in self.allowed_fields} & _FORBIDDEN_REVIEW_FIELDS
        if forbidden:
            raise D132ConfigurationError(
                "D-132 reviewer allowlist contains blinded fields: " + ", ".join(sorted(forbidden))
            )
        missing_guardrails = [key for key in _REQUIRED_GUARDRAILS if self.guardrails.get(key) is not True]
        if missing_guardrails:
            raise D132ConfigurationError(
                "D-132 safety guardrails must all be true: " + ", ".join(missing_guardrails)
            )


@dataclass(frozen=True, slots=True)
class D132SourceSnapshot:
    manifest_path: str
    manifest_sha256: str
    source_run_sha256: str
    provider: str
    source_record_count: int
    selected_records: tuple[dict[str, str], ...]
    selected_record_ids_sha256: str
    sample_file_sha256: tuple[tuple[str, str], ...]

    @property
    def selected_record_count(self) -> int:
        return len(self.selected_records)


@dataclass(frozen=True, slots=True)
class D132RoundState:
    round_id: str
    workspace_id: str
    project_id: str
    config_version: str
    protocol_id: str
    source_manifest_path: str
    source_manifest_sha256: str
    source_run_sha256: str
    source_record_count: int
    selected_record_count: int
    selected_record_ids_sha256: str
    sampling_mode: str
    created_at: datetime


def load_d132_config(
    repo_root: Path,
    config_path: Path | None = None,
) -> D132Config:
    root = Path(repo_root).expanduser().resolve()
    path = (
        _safe_under(root, Path(config_path), label="D-132 config")
        if config_path is not None
        else _safe_relative_file(root, DEFAULT_CONFIG_RELATIVE.as_posix(), label="D-132 config")
    )
    if not path.is_file():
        raise D132ConfigurationError("D-132 config not found")
    raw = _json_object(path, label="D-132 config")
    if int(raw.get("schema_version") or 0) != 1:
        raise D132ConfigurationError("D-132 config requires schema_version=1")
    if raw.get("record_type") != "NUTEV_APPLICATION_WILLIAN_DOCTORATE_A1_D132":
        raise D132ConfigurationError("unexpected D-132 config record_type")

    source = raw.get("source")
    sampling = raw.get("sampling")
    review = raw.get("review")
    guardrails = raw.get("guardrails")
    if not all(isinstance(item, dict) for item in (source, sampling, review, guardrails)):
        raise D132ConfigurationError("D-132 source/sampling/review/guardrails must be objects")

    explicit_values = sampling.get("explicit_record_ids") or []
    decisions = review.get("decision_options") or []
    slots = review.get("reviewer_slots") or []
    allowed = review.get("allowed_fields") or []
    if not all(isinstance(item, list) for item in (explicit_values, decisions, slots, allowed)):
        raise D132ConfigurationError("D-132 list configuration is invalid")

    return D132Config(
        config_version=str(raw.get("config_version") or "").strip(),
        protocol_id=str(raw.get("protocol_id") or "").strip(),
        application_template=str(raw.get("application_template") or "").strip(),
        manifest_path=str(source.get("manifest_path") or "").strip(),
        expected_record_type=str(source.get("expected_record_type") or "").strip(),
        expected_run_id=str(source.get("expected_run_id") or "").strip(),
        expected_source_run_sha256=str(source.get("expected_source_run_sha256") or "").strip(),
        expected_record_count=int(source.get("expected_record_count") or 0),
        sampling_mode=str(sampling.get("mode") or "").strip(),
        explicit_record_ids=tuple(str(item).strip() for item in explicit_values),
        decision_options=tuple(str(item).strip() for item in decisions),
        reason_required=review.get("reason_required") is True,
        minimum_reviewers_per_item=int(review.get("minimum_reviewers_per_item") or 0),
        reviewer_slots=tuple(str(item).strip() for item in slots),
        guest_token_ttl_seconds=int(review.get("guest_token_ttl_seconds") or 0),
        allowed_fields=frozenset(str(item).strip() for item in allowed if str(item).strip()),
        guardrails={str(key): value is True for key, value in guardrails.items()},
    )


def _validate_sample_row(raw: dict[str, Any]) -> dict[str, str]:
    lowered = {str(key).casefold() for key in raw}
    if lowered & _HUMAN_LABEL_KEYS:
        raise D132ConfigurationError("canonical D-132 source must not contain human labels")
    record_id = str(raw.get("record_id") or "").strip()
    if not record_id:
        raise D132ConfigurationError("D-132 source record_id is required")
    return {str(key): str(value or "").strip() for key, value in raw.items()}


def load_d132_source(repo_root: Path, config: D132Config) -> D132SourceSnapshot:
    root = Path(repo_root).expanduser().resolve()
    manifest = _safe_relative_file(root, config.manifest_path, label="D-132 source manifest")
    manifest_raw = manifest.read_bytes()
    payload = _json_object(manifest, label="D-132 source manifest")

    if payload.get("record_type") != config.expected_record_type:
        raise D132ConfigurationError("D-132 source manifest record_type mismatch")
    if payload.get("run_id") != config.expected_run_id:
        raise D132ConfigurationError("D-132 source manifest run_id mismatch")
    source_run_sha = str(payload.get("source_run_sha256") or "").strip()
    if source_run_sha != config.expected_source_run_sha256:
        raise D132ConfigurationError("D-132 source_run_sha256 mismatch")
    if len(source_run_sha) != 64:
        raise D132ConfigurationError("D-132 source_run_sha256 must be SHA-256")
    if int(payload.get("record_count") or 0) != config.expected_record_count:
        raise D132ConfigurationError("D-132 source manifest record_count mismatch")
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise D132ConfigurationError("D-132 source manifest files must be non-empty")

    records: list[dict[str, str]] = []
    file_hashes: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for descriptor in files:
        if not isinstance(descriptor, dict):
            raise D132ConfigurationError("invalid D-132 sample file descriptor")
        relative = str(descriptor.get("path") or "").strip()
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise D132ConfigurationError("D-132 sample path must be safe and relative")
        sample = _safe_under(root, manifest.parent / relative, label="D-132 sample file")
        try:
            sample.relative_to(manifest.parent.resolve())
        except ValueError as exc:
            raise D132ConfigurationError("D-132 sample file must stay beside source manifest") from exc
        if not sample.is_file():
            raise D132ConfigurationError(f"D-132 sample file missing: {relative}")
        expected_sha = str(descriptor.get("sha256") or "").strip()
        actual_sha = _normalized_text_sha256(sample)
        if expected_sha != actual_sha:
            raise D132ConfigurationError(f"D-132 sample hash mismatch: {relative}")
        try:
            with sample.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = [_validate_sample_row(row) for row in csv.DictReader(handle)]
        except (OSError, UnicodeError, csv.Error) as exc:
            raise D132ConfigurationError(f"invalid D-132 sample CSV: {relative}") from exc
        if len(rows) != int(descriptor.get("records") or -1):
            raise D132ConfigurationError(f"D-132 sample row count mismatch: {relative}")
        declared_delta = str(descriptor.get("delta_id") or "").strip()
        for row in rows:
            record_id = row["record_id"]
            if record_id in seen_ids:
                raise D132ConfigurationError(f"duplicate D-132 record_id: {record_id}")
            if declared_delta and row.get("delta_id") != declared_delta:
                raise D132ConfigurationError(f"D-132 delta mismatch for {record_id}")
            seen_ids.add(record_id)
            records.append(row)
        file_hashes.append((relative, actual_sha))

    if len(records) != config.expected_record_count:
        raise D132ConfigurationError("D-132 loaded record count mismatch")

    if config.sampling_mode == "MANIFEST_EXACT":
        selected = records
    else:
        wanted = set(config.explicit_record_ids)
        unknown = sorted(wanted - seen_ids)
        if unknown:
            raise D132ConfigurationError("unknown D-132 explicit record_id: " + ", ".join(unknown))
        selected = [row for row in records if row["record_id"] in wanted]
        if len(selected) != len(config.explicit_record_ids):
            raise D132ConfigurationError("D-132 explicit sample could not be materialized exactly")

    selected_ids = tuple(row["record_id"] for row in selected)
    return D132SourceSnapshot(
        manifest_path=manifest.relative_to(root).as_posix(),
        manifest_sha256=_sha256_bytes(manifest_raw),
        source_run_sha256=source_run_sha,
        provider=str(payload.get("provider") or "").strip(),
        source_record_count=len(records),
        selected_records=tuple(dict(row) for row in selected),
        selected_record_ids_sha256=_record_ids_sha256(selected_ids),
        sample_file_sha256=tuple(file_hashes),
    )


class SQLiteD132Store:
    """Article-1-specific binding state. Raw guest tokens are never persisted here."""

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
            CREATE TABLE IF NOT EXISTS article1_d132_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS article1_d132_rounds (
                round_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                config_version TEXT NOT NULL,
                protocol_id TEXT NOT NULL,
                source_manifest_path TEXT NOT NULL,
                source_manifest_sha256 TEXT NOT NULL,
                source_run_sha256 TEXT NOT NULL,
                source_record_count INTEGER NOT NULL,
                selected_record_count INTEGER NOT NULL,
                selected_record_ids_sha256 TEXT NOT NULL,
                sampling_mode TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(workspace_id, project_id, config_version, source_manifest_sha256)
            );
            CREATE INDEX IF NOT EXISTS idx_article1_d132_scope
                ON article1_d132_rounds(workspace_id, project_id, created_at);
            CREATE TABLE IF NOT EXISTS article1_d132_reviewer_slots (
                round_id TEXT NOT NULL,
                slot TEXT NOT NULL,
                review_reviewer_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                PRIMARY KEY(round_id, slot)
            );
            """
        )
        connection.execute(
            "INSERT INTO article1_d132_meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(D132_SCHEMA_VERSION),),
        )
        connection.commit()
        return connection

    @staticmethod
    def _state(row: sqlite3.Row) -> D132RoundState:
        created = datetime.fromisoformat(str(row["created_at"]))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return D132RoundState(
            round_id=str(row["round_id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            config_version=str(row["config_version"]),
            protocol_id=str(row["protocol_id"]),
            source_manifest_path=str(row["source_manifest_path"]),
            source_manifest_sha256=str(row["source_manifest_sha256"]),
            source_run_sha256=str(row["source_run_sha256"]),
            source_record_count=int(row["source_record_count"]),
            selected_record_count=int(row["selected_record_count"]),
            selected_record_ids_sha256=str(row["selected_record_ids_sha256"]),
            sampling_mode=str(row["sampling_mode"]),
            created_at=created.astimezone(timezone.utc),
        )

    def find_existing(
        self,
        *,
        workspace_id: str,
        project_id: str,
        config_version: str,
        manifest_sha256: str,
    ) -> D132RoundState | None:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM article1_d132_rounds
                WHERE workspace_id = ? AND project_id = ?
                  AND config_version = ? AND source_manifest_sha256 = ?
                """,
                (workspace_id, project_id, config_version, manifest_sha256),
            ).fetchone()
        return self._state(row) if row is not None else None

    def save_round(
        self,
        *,
        round_id: str,
        workspace_id: str,
        project_id: str,
        config: D132Config,
        source: D132SourceSnapshot,
    ) -> D132RoundState:
        require_opaque_id(workspace_id, "workspace")
        require_opaque_id(project_id, "project")
        now = _iso(_now())
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO article1_d132_rounds(
                        round_id, workspace_id, project_id, config_version, protocol_id,
                        source_manifest_path, source_manifest_sha256, source_run_sha256,
                        source_record_count, selected_record_count, selected_record_ids_sha256,
                        sampling_mode, created_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        round_id,
                        workspace_id,
                        project_id,
                        config.config_version,
                        config.protocol_id,
                        source.manifest_path,
                        source.manifest_sha256,
                        source.source_run_sha256,
                        source.source_record_count,
                        source.selected_record_count,
                        source.selected_record_ids_sha256,
                        config.sampling_mode,
                        now,
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise D132ConfigurationError("D-132 round binding already exists") from exc
        return self.get_round(round_id, workspace_id=workspace_id, project_id=project_id)

    def get_round(
        self,
        round_id: str,
        *,
        workspace_id: str | None = None,
        project_id: str | None = None,
    ) -> D132RoundState:
        clauses = ["round_id = ?"]
        values: list[object] = [round_id]
        if workspace_id is not None:
            require_opaque_id(workspace_id, "workspace")
            clauses.append("workspace_id = ?")
            values.append(workspace_id)
        if project_id is not None:
            require_opaque_id(project_id, "project")
            clauses.append("project_id = ?")
            values.append(project_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM article1_d132_rounds WHERE " + " AND ".join(clauses),
                tuple(values),
            ).fetchone()
        if row is None:
            raise FileNotFoundError(round_id)
        return self._state(row)

    def bind_slot(self, *, round_id: str, slot: str, reviewer_id: str) -> None:
        clean_slot = str(slot or "").strip()
        if not clean_slot:
            raise ValueError("reviewer slot is required")
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO article1_d132_reviewer_slots(round_id, slot, review_reviewer_id, created_at)
                    VALUES(?,?,?,?)
                    """,
                    (round_id, clean_slot, reviewer_id, _iso(_now())),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("D-132 reviewer slot already bound") from exc

    def reviewer_for_slot(self, *, round_id: str, slot: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT review_reviewer_id FROM article1_d132_reviewer_slots WHERE round_id = ? AND slot = ?",
                (round_id, str(slot or "").strip()),
            ).fetchone()
        return str(row["review_reviewer_id"]) if row is not None else None

    def slot_for_reviewer(self, *, round_id: str, reviewer_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT slot FROM article1_d132_reviewer_slots WHERE round_id = ? AND review_reviewer_id = ?",
                (round_id, reviewer_id),
            ).fetchone()
        return str(row["slot"]) if row is not None else None

    def list_slots(self, round_id: str) -> dict[str, str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT slot, review_reviewer_id FROM article1_d132_reviewer_slots WHERE round_id = ? ORDER BY slot",
                (round_id,),
            ).fetchall()
        return {str(row["slot"]): str(row["review_reviewer_id"]) for row in rows}


class D132Service:
    """Private Article 1 D-132 assembly over the reusable HumanReviewEngine."""

    def __init__(
        self,
        *,
        repo_root: Path,
        database_path: Path,
        config_path: Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).expanduser().resolve()
        self.config_path = Path(config_path).expanduser().resolve() if config_path is not None else None
        self.store = SQLiteD132Store(database_path)
        self.engine = HumanReviewEngine(SQLiteHumanReviewStore(database_path))

    def config(self) -> D132Config:
        return load_d132_config(self.repo_root, self.config_path)

    def source(self) -> D132SourceSnapshot:
        return load_d132_source(self.repo_root, self.config())

    def create_round(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
    ) -> D132RoundState:
        config = self.config()
        source = load_d132_source(self.repo_root, config)
        existing = self.store.find_existing(
            workspace_id=workspace_id,
            project_id=project_id,
            config_version=config.config_version,
            manifest_sha256=source.manifest_sha256,
        )
        if existing is not None:
            self.engine.round_summary(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                project_access_confirmed=project_access_confirmed,
                round_id=existing.round_id,
            )
            return existing

        review_round = self.engine.create_round(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=project_access_confirmed,
            name="Article 1 — D-132 independent human verification",
            policy=ReviewPolicy(
                decision_options=config.decision_options,
                reason_required=config.reason_required,
                minimum_reviewers_per_item=config.minimum_reviewers_per_item,
            ),
        )
        return self.store.save_round(
            round_id=review_round.id,
            workspace_id=workspace_id,
            project_id=project_id,
            config=config,
            source=source,
        )

    @staticmethod
    def _reviewer_order(
        records: tuple[dict[str, str], ...],
        source_run_sha256: str,
        slot: str,
    ) -> list[dict[str, str]]:
        if slot == "A":
            seed = int(source_run_sha256[:16], 16)
        elif slot == "B":
            seed = int(source_run_sha256[16:32], 16)
        else:
            raise ValueError("unsupported D-132 reviewer slot")
        ordered = [dict(row) for row in records]
        random.Random(seed).shuffle(ordered)
        if slot == "B" and len(ordered) > 1:
            reference = [dict(row) for row in records]
            random.Random(int(source_run_sha256[:16], 16)).shuffle(reference)
            if [row["record_id"] for row in reference] == [row["record_id"] for row in ordered]:
                ordered = ordered[1:] + ordered[:1]
        return ordered

    def _source_for_state(self, state: D132RoundState) -> tuple[D132Config, D132SourceSnapshot]:
        config = self.config()
        source = load_d132_source(self.repo_root, config)
        if config.config_version != state.config_version:
            raise D132ConfigurationError("D-132 round config version no longer matches source configuration")
        if source.manifest_sha256 != state.source_manifest_sha256:
            raise D132ConfigurationError("D-132 source manifest changed after round creation")
        if source.source_run_sha256 != state.source_run_sha256:
            raise D132ConfigurationError("D-132 source run changed after round creation")
        if source.selected_record_count != state.selected_record_count:
            raise D132ConfigurationError("D-132 selected record count changed after round creation")
        if source.selected_record_ids_sha256 != state.selected_record_ids_sha256:
            raise D132ConfigurationError("D-132 selected record identity changed after round creation")
        return config, source

    def issue_guest_reviewer(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
        slot: str,
        label: str,
        ttl_seconds: int | None = None,
    ) -> IssuedGuestReviewToken:
        state = self.store.get_round(round_id, workspace_id=workspace_id, project_id=project_id)
        config, source = self._source_for_state(state)
        clean_slot = str(slot or "").strip()
        if clean_slot not in config.reviewer_slots:
            raise ValueError("invalid D-132 reviewer slot")
        if self.store.reviewer_for_slot(round_id=round_id, slot=clean_slot) is not None:
            raise ValueError("D-132 reviewer slot already issued")

        issued = self.engine.issue_guest_reviewer(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=project_access_confirmed,
            round_id=round_id,
            label=label,
            ttl_seconds=ttl_seconds or config.guest_token_ttl_seconds,
        )
        try:
            ordered = self._reviewer_order(source.selected_records, source.source_run_sha256, clean_slot)
            for position, record in enumerate(ordered, 1):
                payload = dict(record)
                payload["packet_position"] = str(position)
                self.engine.assign_item(
                    principal,
                    workspace_id=workspace_id,
                    project_id=project_id,
                    project_access_confirmed=project_access_confirmed,
                    round_id=round_id,
                    reviewer_id=issued.reviewer.id,
                    item_key=record["record_id"],
                    payload=payload,
                    allowed_fields=config.allowed_fields,
                )
            self.store.bind_slot(
                round_id=round_id,
                slot=clean_slot,
                reviewer_id=issued.reviewer.id,
            )
        except Exception:
            self.engine.revoke_guest_reviewer(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                project_access_confirmed=project_access_confirmed,
                round_id=round_id,
                reviewer_id=issued.reviewer.id,
            )
            raise
        return issued

    def _guest_access(self, token: str):
        access = self.engine.access_for_guest(token)
        self.store.get_round(
            access.round_id,
            workspace_id=access.workspace_id,
            project_id=access.project_id,
        )
        slot = self.store.slot_for_reviewer(
            round_id=access.round_id,
            reviewer_id=access.reviewer_id,
        )
        if slot is None:
            raise FileNotFoundError(access.round_id)
        return access, slot

    def guest_payload(self, token: str) -> dict[str, Any]:
        access, slot = self._guest_access(token)
        payload = self.engine.review_payload(access)
        return {
            "protocol_id": "D-132",
            "reviewer_slot": slot,
            **payload,
        }

    def save_guest_decision(
        self,
        token: str,
        *,
        assignment_id: str,
        decision_value: str,
        reason: str,
        notes: str = "",
    ) -> dict[str, Any]:
        access, _ = self._guest_access(token)
        return self.engine.save_decision(
            access,
            assignment_id=assignment_id,
            decision_value=decision_value,
            reason=reason,
            notes=notes,
        )

    def submit_guest(self, token: str) -> dict[str, Any]:
        access, _ = self._guest_access(token)
        return self.engine.submit(access)

    def summary(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
    ) -> dict[str, Any]:
        state = self.store.get_round(round_id, workspace_id=workspace_id, project_id=project_id)
        engine_summary = self.engine.round_summary(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=project_access_confirmed,
            round_id=round_id,
        )
        return {
            "protocol_id": state.protocol_id,
            "round_id": state.round_id,
            "sampling_mode": state.sampling_mode,
            "source_record_count": state.source_record_count,
            "selected_record_count": state.selected_record_count,
            "source_manifest_sha256": state.source_manifest_sha256,
            "source_run_sha256": state.source_run_sha256,
            "selected_record_ids_sha256": state.selected_record_ids_sha256,
            "reviewer_slots": self.store.list_slots(round_id),
            "review": engine_summary,
            "scientific_gate_effects": {
                "press_pass": False,
                "c4_decision": False,
                "gf10_authorized": False,
                "query_frozen": False,
                "formal_search_executed": False,
                "prisma_created": False,
            },
        }

    def adjudication_payload(
        self,
        principal: Principal,
        *,
        workspace_id: str,
        project_id: str,
        project_access_confirmed: bool,
        round_id: str,
    ) -> dict[str, Any]:
        self.store.get_round(round_id, workspace_id=workspace_id, project_id=project_id)
        return self.engine.adjudication_payload(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=project_access_confirmed,
            round_id=round_id,
        )

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
        self.store.get_round(round_id, workspace_id=workspace_id, project_id=project_id)
        return self.engine.save_adjudication(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=project_access_confirmed,
            round_id=round_id,
            item_key=item_key,
            decision_value=decision_value,
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
        self.store.get_round(round_id, workspace_id=workspace_id, project_id=project_id)
        return self.engine.finalize_adjudication(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=project_access_confirmed,
            round_id=round_id,
        )
