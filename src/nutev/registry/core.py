from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any

from .identity import observed_aliases
from .sqlite_store import SQLiteArticleRegistry


class RegistryCoreError(RuntimeError):
    """Raised when CORE material cannot be safely projected into the Registry."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryCoreError(f"invalid CORE manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryCoreError("CORE manifest must be a JSON object")
    if value.get("core_type") != "NUTEV_CORE_EVIDENCE_BANK":
        raise RegistryCoreError("unexpected CORE manifest type")
    if value.get("status") != "PASS":
        raise RegistryCoreError("CORE manifest is not PASS")
    return value


def _read_core_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise RegistryCoreError(f"missing CORE records: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RegistryCoreError(
                    f"invalid CORE JSONL at line {line_number}: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise RegistryCoreError(f"CORE row {line_number} is not an object")
            rows.append(value)
    return rows


def _verify_core_source(records_path: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = _read_manifest(manifest_path)
    expected = str(
        (((manifest.get("outputs") or {}).get("core_records") or {}).get("sha256")) or ""
    ).strip().lower()
    if len(expected) != 64:
        raise RegistryCoreError("CORE manifest has no valid core_records SHA-256")
    actual = _sha256_file(records_path)
    if actual != expected:
        raise RegistryCoreError(
            f"CORE records SHA-256 mismatch: expected {expected}, got {actual}"
        )
    return manifest


def _identity_probe(record: dict[str, Any]) -> dict[str, Any]:
    identity = record.get("identity") or {}
    bibliographic = record.get("bibliographic") or {}
    if not isinstance(identity, dict):
        identity = {}
    if not isinstance(bibliographic, dict):
        bibliographic = {}
    return {
        "title": identity.get("title"),
        "doi": identity.get("doi"),
        "pmid": identity.get("pmid"),
        "url": identity.get("url"),
        "year": identity.get("year"),
        "journal": bibliographic.get("journal"),
        "source_provider": identity.get("source_provider"),
    }


def _resolve_article_ids(
    connection: sqlite3.Connection,
    record: dict[str, Any],
) -> tuple[str, ...]:
    direct = str(record.get("article_id") or "").strip()
    if direct:
        row = connection.execute(
            "SELECT article_id FROM articles WHERE article_id = ?",
            (direct,),
        ).fetchone()
        if row:
            return (direct,)

    article_ids: set[str] = set()
    for alias in observed_aliases(_identity_probe(record)):
        row = connection.execute(
            "SELECT article_id FROM article_aliases WHERE scheme = ? AND normalized_value = ?",
            (alias.scheme, alias.normalized_value),
        ).fetchone()
        if row:
            article_ids.add(str(row["article_id"]))
    return tuple(sorted(article_ids))


def _input_artifact_hashes(record: dict[str, Any]) -> dict[str, Any]:
    provenance = record.get("provenance") or {}
    acquisition = record.get("acquisition") or {}
    if not isinstance(provenance, dict):
        provenance = {}
    if not isinstance(acquisition, dict):
        acquisition = {}
    source_files = provenance.get("source_files_sha256") or {}
    if not isinstance(source_files, dict):
        source_files = {}
    return {
        "source_files_sha256": source_files,
        "artifact_sha256": acquisition.get("artifact_sha256"),
        "text_sha256": acquisition.get("text_sha256"),
    }


def _semantic_record_hash(record: dict[str, Any]) -> str:
    """Hash scientific/indexing substance, not run time or contextual search rank."""

    payload = {
        "schema_version": record.get("schema_version"),
        "identity": record.get("identity") or {},
        "bibliographic": record.get("bibliographic") or {},
        "provenance": {
            "evidence_record_id": (record.get("provenance") or {}).get("evidence_record_id")
            if isinstance(record.get("provenance"), dict)
            else None,
            "origin_sha256": (record.get("provenance") or {}).get("origin_sha256")
            if isinstance(record.get("provenance"), dict)
            else None,
            "source_files_sha256": _input_artifact_hashes(record)["source_files_sha256"],
        },
        "acquisition": record.get("acquisition") or {},
        "structure": record.get("structure") or {},
        "classification": record.get("classification") or {},
        "main_findings": record.get("main_findings") or [],
        "scores": record.get("scores") or {},
        "workflow": record.get("workflow") or {},
        "content_refs": record.get("content_refs") or {},
        "guardrails": record.get("guardrails") or {},
    }
    return sha256(_json(payload).encode("utf-8")).hexdigest()


def _pipeline_version(record: dict[str, Any], manifest: dict[str, Any]) -> str:
    return (
        f"NUTEV_CORE_RECORD_SCHEMA_{int(record.get('schema_version') or 1)}"
        f"__CORE_MANIFEST_SCHEMA_{int(manifest.get('schema_version') or 1)}"
    )


def _current_version(
    connection: sqlite3.Connection,
    article_id: str,
) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT * FROM core_versions WHERE article_id = ? AND is_current = 1",
        (article_id,),
    ).fetchone()


def project_core_records(
    *,
    output_root: Path,
    core_records_path: Path,
    core_manifest_path: Path,
) -> dict[str, Any]:
    """Accumulate verified CORE versions under durable Article Registry identity."""

    root = Path(output_root).resolve()
    registry_db = root / "registry" / "article_registry.sqlite"
    if not registry_db.is_file():
        return {
            "status": "SKIPPED_MISSING_REGISTRY",
            "created_versions": 0,
            "matched_current": 0,
            "historical_matches": 0,
            "unresolved": 0,
            "identity_conflicts": 0,
        }

    manifest = _verify_core_source(Path(core_records_path), Path(core_manifest_path))
    records = _read_core_records(Path(core_records_path))
    registry = SQLiteArticleRegistry(
        registry_db,
        root / "registry" / "ARTICLE_REGISTRY_MANIFEST.json",
    )
    if registry.integrity_check() != "ok":
        raise RegistryCoreError("Article Registry integrity_check failed")

    created = 0
    matched_current = 0
    historical_matches = 0
    unresolved = 0
    conflicts = 0
    projected: list[dict[str, Any]] = []

    with registry._connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        for record in records:
            candidates = _resolve_article_ids(connection, record)
            if not candidates:
                unresolved += 1
                projected.append(
                    {
                        "core_record_id": record.get("id"),
                        "document_id": record.get("document_id"),
                        "status": "UNRESOLVED",
                    }
                )
                continue
            if len(candidates) > 1:
                conflicts += 1
                projected.append(
                    {
                        "core_record_id": record.get("id"),
                        "document_id": record.get("document_id"),
                        "status": "IDENTITY_CONFLICT",
                        "candidate_article_ids": list(candidates),
                    }
                )
                continue

            article_id = candidates[0]
            record_sha = _semantic_record_hash(record)
            same = connection.execute(
                "SELECT core_version_id, version_number, is_current FROM core_versions "
                "WHERE article_id = ? AND record_sha256 = ?",
                (article_id, record_sha),
            ).fetchone()
            if same is not None:
                if int(same["is_current"] or 0) == 1:
                    matched_current += 1
                    status = "MATCHED_CURRENT"
                else:
                    historical_matches += 1
                    status = "MATCHED_HISTORICAL_NO_ROLLBACK"
                projected.append(
                    {
                        "article_id": article_id,
                        "core_record_id": record.get("id"),
                        "status": status,
                        "core_version_id": same["core_version_id"],
                        "version_number": int(same["version_number"]),
                    }
                )
                continue

            next_version = int(
                connection.execute(
                    "SELECT COALESCE(MAX(version_number), 0) + 1 FROM core_versions WHERE article_id = ?",
                    (article_id,),
                ).fetchone()[0]
            )
            current = _current_version(connection, article_id)
            connection.execute(
                "UPDATE core_versions SET is_current = 0 WHERE article_id = ? AND is_current = 1",
                (article_id,),
            )
            core_version_id = f"NUTEV-COREV-{sha256(f'{article_id}|{next_version}|{record_sha}'.encode()).hexdigest()[:24]}"
            stored = deepcopy(record)
            stored["article_id"] = article_id
            stored["registry_core_version"] = {
                "core_version_id": core_version_id,
                "version_number": next_version,
                "record_sha256": record_sha,
                "previous_core_version_id": current["core_version_id"] if current else None,
            }
            generated_at = str(record.get("generated_at") or _now())
            connection.execute(
                """
                INSERT INTO core_versions(
                    core_version_id, article_id, version_number, core_record_id,
                    source_document_id, record_sha256, input_artifact_hashes_json,
                    pipeline_version, generated_at, record_json, is_current, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    core_version_id,
                    article_id,
                    next_version,
                    str(record.get("id") or ""),
                    str(record.get("document_id") or ""),
                    record_sha,
                    _json(_input_artifact_hashes(record)),
                    _pipeline_version(record, manifest),
                    generated_at,
                    _json(stored),
                    _now(),
                ),
            )
            created += 1
            projected.append(
                {
                    "article_id": article_id,
                    "core_record_id": record.get("id"),
                    "status": "CREATED_VERSION",
                    "core_version_id": core_version_id,
                    "version_number": next_version,
                }
            )
        connection.commit()

    registry._write_manifest()
    overall = "COMPLETE_WITH_IDENTITY_GAPS" if unresolved or conflicts else "COMPLETE"
    return {
        "status": overall,
        "source_core_records": len(records),
        "created_versions": created,
        "matched_current": matched_current,
        "historical_matches": historical_matches,
        "unresolved": unresolved,
        "identity_conflicts": conflicts,
        "registry_integrity": registry.integrity_check(),
        "core_manifest_sha256": _sha256_file(Path(core_manifest_path)),
        "core_records_sha256": _sha256_file(Path(core_records_path)),
        "projections": projected,
        "guardrail": (
            "CORE versioning preserves machine-derived scientific information history. "
            "It does not create eligibility, quality, certainty, causality, recommendation, "
            "human validation, or PRISMA events."
        ),
    }


def list_core_versions(*, output_root: Path, article_id: str) -> list[dict[str, Any]]:
    database = Path(output_root) / "registry" / "article_registry.sqlite"
    if not database.is_file():
        return []
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT core_version_id, article_id, version_number, core_record_id, "
            "source_document_id, record_sha256, input_artifact_hashes_json, pipeline_version, "
            "generated_at, is_current, created_at FROM core_versions "
            "WHERE article_id = ? ORDER BY version_number",
            (article_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
