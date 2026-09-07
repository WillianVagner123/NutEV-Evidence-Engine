from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from typing import Any, Iterable, Iterator

from .full_text import record_full_text_artifact
from .ingest import SearchRegistryIngestor
from .sqlite_store import SQLiteArticleRegistry


CANONICAL_SOURCE_PATHS = (
    "15_web_searches",
    "bank/searches",
    "scientific",
    "scientific/core",
    "scientific/workbench",
    "16_search_full_text_cache",
    "agent_context/article1",
)
SUPPORTED_SUFFIXES = {".json", ".jsonl", ".ndjson", ".csv"}
IDENTIFIER_KEYS = {
    "doi",
    "doi_normalized",
    "pmid",
    "pmid_normalized",
    "pmcid",
    "pmc_id",
    "openalex_id",
    "openalex",
    "semantic_scholar_id",
    "semantic_scholar_paper_id",
    "crossref_id",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return sha256(raw).hexdigest()


def _file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _bucket(path: Path) -> str:
    normalized = "/" + path.as_posix().casefold().strip("/") + "/"
    if "/16_search_full_text_cache/" in normalized or "full_text_cache" in normalized:
        return "full_text_cache"
    if "/scientific/core/" in normalized:
        return "scientific_core"
    if "/scientific/workbench/" in normalized:
        return "scientific_workbench"
    if "/15_web_searches/" in normalized:
        return "web_searches"
    if "/bank/searches/" in normalized:
        return "bank_searches"
    if "/agent_context/article1/" in normalized or "/article1/" in normalized:
        return "article1"
    if "/scientific/" in normalized:
        return "scientific_other"
    return "other"


def _load_payloads(path: Path) -> list[Any]:
    suffix = path.suffix.casefold()
    if suffix == ".json":
        return [json.loads(path.read_text(encoding="utf-8-sig"))]
    if suffix in {".jsonl", ".ndjson"}:
        payloads: list[Any] = []
        for line_number, raw in enumerate(
            path.read_text(encoding="utf-8-sig").splitlines(), start=1
        ):
            line = raw.strip()
            if not line:
                continue
            try:
                payloads.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL line {line_number}: {exc}") from exc
        return payloads
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [list(csv.DictReader(handle))]
    return []


def _looks_like_search(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("results"), list)
        and bool(value.get("search_id") or value.get("query") or value.get("question"))
    )


def _looks_like_full_text_manifest(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return bool(
        value.get("content_sha256")
        and (value.get("private_text_sha256") or value.get("text_sha256"))
    )


def _looks_like_article(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if any(value.get(key) not in (None, "") for key in IDENTIFIER_KEYS):
        return True
    title = str(value.get("title") or "").strip()
    if not title:
        return False
    return bool(
        value.get("year")
        or value.get("publication_year")
        or value.get("journal")
        or value.get("venue")
    )


def _walk_dicts(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_dicts(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_dicts(nested)


def _search_objects(value: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if _looks_like_search(node):
            output.append(node)
            return
        if isinstance(node, dict):
            for nested in node.values():
                visit(nested)
        elif isinstance(node, list):
            for nested in node:
                visit(nested)

    visit(value)
    return output


def _article_records(value: Any) -> list[dict[str, Any]]:
    return [record for record in _walk_dicts(value) if _looks_like_article(record)]


def _full_text_manifests(value: Any) -> list[dict[str, Any]]:
    return [record for record in _walk_dicts(value) if _looks_like_full_text_manifest(record)]


def _legacy_search_id(path: Path, search: dict[str, Any]) -> str:
    existing = str(search.get("search_id") or "").strip()
    if existing:
        return existing
    seed = {
        "path": path.as_posix(),
        "query": search.get("query") or search.get("question") or "",
        "created_at": search.get("created_at") or search.get("timestamp") or "",
    }
    return "NUTEV-LEGACY-" + _json_hash(seed)[:20]


def _normalize_search(path: Path, search: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(search)
    rows = [deepcopy(row) for row in result.get("results") or [] if isinstance(row, dict)]
    for index, row in enumerate(rows, start=1):
        if not row.get("reference_rank"):
            row["reference_rank"] = index
    result["results"] = rows
    result["search_id"] = _legacy_search_id(path, result)
    result["query"] = str(result.get("query") or result.get("question") or "").strip()
    result["search_mode"] = str(result.get("search_mode") or "legacy_migrated")
    result["status"] = str(result.get("status") or "LEGACY_MIGRATED")
    result["created_at"] = str(
        result.get("created_at") or result.get("timestamp") or _now()
    )
    result["records_before_dedup"] = int(
        result.get("records_before_dedup") or len(rows)
    )
    result["unique_records"] = int(result.get("unique_records") or len(rows))
    result["returned_records"] = int(result.get("returned_records") or len(rows))
    plan = result.get("query_plan")
    if not isinstance(plan, dict):
        plan = {}
    plan = deepcopy(plan)
    plan.setdefault("migration_source_path", path.as_posix())
    plan.setdefault("legacy_import", True)
    result["query_plan"] = plan
    return result


def _source_presence(root: Path) -> dict[str, bool]:
    return {
        relative: (root / relative).exists()
        for relative in CANONICAL_SOURCE_PATHS
    }


def _candidate_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() in SUPPORTED_SUFFIXES
    )


def _registration_to_dict(registration: Any) -> dict[str, Any]:
    try:
        return asdict(registration)
    except TypeError:
        return {
            key: getattr(registration, key)
            for key in (
                "status",
                "article_id",
                "conflict_id",
                "created",
                "enriched",
                "aliases_added",
                "manifestation_added",
            )
            if hasattr(registration, key)
        }


def _full_text_count(database_path: Path) -> int:
    connection = sqlite3.connect(database_path)
    try:
        return int(connection.execute("SELECT COUNT(*) FROM full_text_artifacts").fetchone()[0])
    finally:
        connection.close()


def run_history_migration_dry_run(
    *,
    source_roots: Iterable[Path],
    report_path: Path,
) -> dict[str, Any]:
    """Rehearse historical Registry migration without mutating source or target data.

    All identity operations are executed against a disposable Registry using the same
    production identity engine. Legacy files are read only. No production Registry,
    Workbench, CORE artifact, cache, or source file is changed or deleted.
    """

    roots = [Path(root).resolve() for root in source_roots]
    inventory: list[dict[str, Any]] = []
    file_errors: list[dict[str, str]] = []
    quarantined: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    full_text_queue: list[tuple[Path, Path, dict[str, Any]]] = []
    counters: Counter[str] = Counter()
    source_presence = {str(root): _source_presence(root) for root in roots}

    with TemporaryDirectory(prefix="nutev_registry_migration_") as tmp:
        temp_output = Path(tmp) / "output"
        registry_db = temp_output / "registry" / "article_registry.sqlite"
        registry_manifest = temp_output / "registry" / "ARTICLE_REGISTRY_MANIFEST.json"
        registry = SQLiteArticleRegistry(registry_db, registry_manifest)
        search_registry = SearchRegistryIngestor(registry_db, registry_manifest)

        for root in roots:
            for path in _candidate_files(root):
                bucket = _bucket(path)
                counters[f"files_{bucket}"] += 1
                entry = {
                    "root": str(root),
                    "path": _relative(path, root),
                    "bucket": bucket,
                    "sha256": _file_hash(path),
                    "bytes": path.stat().st_size,
                }
                inventory.append(entry)
                try:
                    payloads = _load_payloads(path)
                except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
                    file_errors.append({"path": str(path), "error": str(exc)})
                    counters["quarantined_records"] += 1
                    quarantined.append(
                        {"path": str(path), "reason": "unreadable_source", "error": str(exc)}
                    )
                    continue

                for payload in payloads:
                    if bucket == "full_text_cache":
                        manifests = _full_text_manifests(payload)
                        full_text_queue.extend((root, path, manifest) for manifest in manifests)
                        counters["full_text_manifests_seen"] += len(manifests)
                        if manifests:
                            continue

                    searches = _search_objects(payload)
                    if searches:
                        for search in searches:
                            normalized = _normalize_search(path, search)
                            counters["search_runs_seen"] += 1
                            counters["records_seen"] += len(normalized["results"])
                            try:
                                summary = search_registry.ingest_search_result(normalized)
                            except (TypeError, ValueError, sqlite3.DatabaseError) as exc:
                                counters["quarantined_records"] += len(normalized["results"]) or 1
                                quarantined.append(
                                    {
                                        "path": str(path),
                                        "search_id": normalized["search_id"],
                                        "reason": "search_ingest_failed",
                                        "error": str(exc),
                                    }
                                )
                                continue
                            for row in normalized["results"]:
                                if row.get("registry_identity_status") == "CONFLICT":
                                    counters["quarantined_records"] += 1
                                    conflicts.append(
                                        {
                                            "path": str(path),
                                            "search_id": normalized["search_id"],
                                            "conflict_id": row.get("registry_conflict_id"),
                                            "title": row.get("title"),
                                            "doi": row.get("doi"),
                                            "pmid": row.get("pmid"),
                                        }
                                    )
                                elif row.get("registry_identity_status") == "UNRESOLVED":
                                    counters["quarantined_records"] += 1
                                    quarantined.append(
                                        {
                                            "path": str(path),
                                            "search_id": normalized["search_id"],
                                            "reason": "article_identity_unresolved",
                                            "title": row.get("title"),
                                        }
                                    )
                            counters["search_hits_ingested"] += int(
                                summary.get("search_hits_recorded") or 0
                            )
                        continue

                    articles = _article_records(payload)
                    for article in articles:
                        counters["records_seen"] += 1
                        try:
                            registration = registry.register_article(
                                deepcopy(article), provider=str(article.get("source_provider") or "")
                            )
                        except (TypeError, ValueError, sqlite3.DatabaseError) as exc:
                            counters["quarantined_records"] += 1
                            quarantined.append(
                                {
                                    "path": str(path),
                                    "reason": "article_ingest_failed",
                                    "error": str(exc),
                                    "title": article.get("title"),
                                }
                            )
                            continue
                        registration_payload = _registration_to_dict(registration)
                        if registration_payload.get("status") == "CONFLICT":
                            counters["quarantined_records"] += 1
                            conflicts.append(
                                {
                                    "path": str(path),
                                    "conflict_id": registration_payload.get("conflict_id"),
                                    "title": article.get("title"),
                                    "doi": article.get("doi"),
                                    "pmid": article.get("pmid"),
                                }
                            )

        for root, path, manifest in full_text_queue:
            counters["records_seen"] += 1
            identity_record = {
                key: value
                for key, value in manifest.items()
                if key in IDENTIFIER_KEYS
                or key
                in {
                    "title",
                    "year",
                    "publication_year",
                    "journal",
                    "venue",
                    "source_provider",
                    "provider",
                    "source",
                    "url",
                }
            }
            try:
                registration = registry.register_article(identity_record)
            except (TypeError, ValueError, sqlite3.DatabaseError):
                counters["unmatched_full_text_cache"] += 1
                quarantined.append(
                    {"path": str(path), "reason": "full_text_identity_unresolved"}
                )
                continue
            registration_payload = _registration_to_dict(registration)
            article_id = str(registration_payload.get("article_id") or "")
            if registration_payload.get("status") == "CONFLICT" or not article_id:
                counters["unmatched_full_text_cache"] += 1
                counters["quarantined_records"] += 1
                conflicts.append(
                    {
                        "path": str(path),
                        "conflict_id": registration_payload.get("conflict_id"),
                        "reason": "full_text_identity_conflict",
                    }
                )
                continue
            linked = record_full_text_artifact(
                output_root=temp_output,
                article_id=article_id,
                manifest=manifest,
                cache_dir=path.parent,
            )
            if linked.get("status") != "linked":
                counters["unmatched_full_text_cache"] += 1
                quarantined.append(
                    {
                        "path": str(path),
                        "reason": linked.get("reason") or "full_text_not_linked",
                    }
                )

        stats = registry.stats()
        integrity = registry.integrity_check()
        full_text_linked = _full_text_count(registry_db)

    any_materialized_source = any(
        any(values.values()) for values in source_presence.values()
    )
    if not roots or not any_materialized_source:
        status = "SOURCE_NOT_MATERIALIZED"
    elif integrity != "ok":
        status = "DRY_RUN_FAIL"
    elif stats.identity_conflicts_open or counters["quarantined_records"] or file_errors:
        status = "REVIEW_REQUIRED"
    else:
        status = "DRY_RUN_PASS"

    report: dict[str, Any] = {
        "report_type": "NUTEV_REGISTRY_HISTORICAL_MIGRATION_DRY_RUN",
        "status": status,
        "generated_at": _now(),
        "source_roots": [str(root) for root in roots],
        "source_presence": source_presence,
        "source_inventory": {
            "files_seen": len(inventory),
            "files_by_bucket": dict(
                sorted(
                    (key.removeprefix("files_"), value)
                    for key, value in counters.items()
                    if key.startswith("files_")
                )
            ),
            "files": inventory,
            "file_errors": file_errors,
        },
        "records_seen": int(counters["records_seen"]),
        "unique_articles_created": stats.articles,
        "aliases_created": stats.aliases,
        "search_hits_created": stats.search_hits,
        "manifestations_created": stats.manifestations,
        "full_text_artifacts_linked": full_text_linked,
        "identity_conflicts": stats.identity_conflicts_open,
        "unmatched_full_text_cache": int(counters["unmatched_full_text_cache"]),
        "quarantined_records": int(counters["quarantined_records"]),
        "search_runs_seen": int(counters["search_runs_seen"]),
        "search_runs_created": stats.search_runs,
        "full_text_manifests_seen": int(counters["full_text_manifests_seen"]),
        "registry_integrity_check": integrity,
        "conflicts": conflicts,
        "quarantine": quarantined,
        "guardrails": {
            "dry_run": True,
            "temporary_registry_only": True,
            "target_registry_mutated": False,
            "legacy_files_modified": False,
            "legacy_files_deleted": False,
            "fuzzy_identity_merge": False,
            "scientific_inclusion_changed": False,
            "prisma_state_changed": False,
        },
        "next_gate": (
            "mount_real_project_output_and_review_report"
            if status == "SOURCE_NOT_MATERIALIZED"
            else "human_reconciliation_before_apply"
        ),
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
