from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable

from .identity import has_strong_conflict, observed_aliases
from .models import ArticleRegistration, RegistryAlias
from .sqlite_store import (
    SQLiteArticleRegistry,
    _json,
    _payload_hash,
    _provider_name,
    _provider_record_id,
    _text,
)


_TRANSIENT_RESULT_FIELDS = {
    "article_id",
    "registry_identity_status",
    "registry_conflict_id",
    "registry_summary",
    "full_text",
}


def _now(value: str | None = None) -> str:
    return str(value or datetime.now(timezone.utc).isoformat())


def _stable_record(record: dict[str, Any]) -> dict[str, Any]:
    """Remove registry/full-text annotations that must not create new manifestations."""

    return {
        key: value
        for key, value in record.items()
        if key not in _TRANSIENT_RESULT_FIELDS
    }


def _search_context_sha256(result: dict[str, Any]) -> str:
    payload = {
        "search_id": result.get("search_id"),
        "query": result.get("query"),
        "created_at": result.get("created_at"),
        "search_mode": result.get("search_mode"),
        "status": result.get("status"),
        "providers": result.get("providers"),
        "query_plan": result.get("query_plan"),
        "records_before_dedup": result.get("records_before_dedup"),
        "unique_records": result.get("unique_records"),
        "returned_records": result.get("returned_records"),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


def _provider_gaps(result: dict[str, Any]) -> list[Any]:
    gaps: list[Any] = []
    for key in (
        "failed_providers",
        "unavailable_providers",
        "partial_providers",
        "skipped_providers",
        "non_exhaustive_providers",
    ):
        for item in result.get(key) or []:
            if item not in gaps:
                gaps.append(item)
    for item in result.get("audit_gaps") or []:
        if item not in gaps:
            gaps.append(item)
    return gaps


def _manifestation_rows(row: dict[str, Any]) -> list[dict[str, Any]]:
    values = row.get("source_manifestations")
    if not isinstance(values, list):
        return []
    output: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        merged: dict[str, Any] = {
            key: row.get(key)
            for key in ("title", "abstract", "authors", "journal", "venue", "year")
            if row.get(key) not in (None, "")
        }
        merged.update(value)
        merged.pop("source_manifestations", None)
        output.append(_stable_record(merged))
    return output


def _manifestation_id(article_id: str, record: dict[str, Any], provider: str) -> str:
    source_hash = _payload_hash(record)
    provider_record_id = _provider_record_id(record)
    seed = f"{article_id}|{provider}|{provider_record_id}|{source_hash}"
    return "NUTEV-MAN-" + sha256(seed.encode("utf-8")).hexdigest()[:24]


class SearchRegistryIngestor(SQLiteArticleRegistry):
    """Batch search ingestion over the durable Article Registry.

    Search ranking remains contextual. This class only attaches durable article
    identity, provider manifestations, search-run provenance, and SearchHits.
    """

    def _conflict(
        self,
        connection: sqlite3.Connection,
        *,
        candidate_article_ids: Iterable[str],
        aliases: Iterable[RegistryAlias],
        reason: str,
        observed_at: str,
    ) -> str:
        """Keep a logical conflict idempotent even when discovered by another path."""

        article_ids = tuple(sorted(set(candidate_article_ids)))
        identifiers = tuple(sorted((alias.scheme, alias.normalized_value) for alias in aliases))
        article_ids_json = _json(article_ids)
        identifiers_json = _json(identifiers)
        existing = connection.execute(
            "SELECT conflict_id FROM identity_conflicts "
            "WHERE candidate_article_ids_json = ? AND identifiers_json = ? AND status = 'open' "
            "ORDER BY created_at LIMIT 1",
            (article_ids_json, identifiers_json),
        ).fetchone()
        if existing:
            conflict_id = str(existing["conflict_id"])
            connection.execute(
                "UPDATE identity_conflicts SET updated_at = ?, reason = ? WHERE conflict_id = ?",
                (observed_at, reason, conflict_id),
            )
        else:
            payload = _json({"candidate_article_ids": article_ids, "identifiers": identifiers})
            fingerprint = sha256(payload.encode("utf-8")).hexdigest()
            conflict_id = "NUTEV-CONFLICT-" + fingerprint[:20]
            connection.execute(
                "INSERT INTO identity_conflicts("
                "conflict_id, fingerprint, candidate_article_ids_json, identifiers_json, reason, "
                "status, created_at, updated_at"
                ") VALUES (?, ?, ?, ?, ?, 'open', ?, ?) "
                "ON CONFLICT(fingerprint) DO UPDATE SET updated_at = excluded.updated_at, reason = excluded.reason",
                (
                    conflict_id,
                    fingerprint,
                    article_ids_json,
                    identifiers_json,
                    reason,
                    observed_at,
                    observed_at,
                ),
            )
        for article_id in article_ids:
            connection.execute(
                "UPDATE articles SET registry_status = 'identity_conflict', updated_at = ? "
                "WHERE article_id = ?",
                (observed_at, article_id),
            )
        return conflict_id

    def _register_one(
        self,
        connection: sqlite3.Connection,
        record: dict[str, Any],
        *,
        provider: str = "",
        observed_at: str,
    ) -> ArticleRegistration:
        effective_provider = _provider_name(record, provider)
        aliases = observed_aliases(record, provider=effective_provider)
        if not aliases:
            raise ValueError("article identity unavailable: title or exact alias required")
        candidates = self._candidate_article_ids(connection, aliases)

        if len(candidates) > 1:
            conflict_id = self._conflict(
                connection,
                candidate_article_ids=candidates,
                aliases=aliases,
                reason="observed_aliases_resolve_multiple_articles",
                observed_at=observed_at,
            )
            return ArticleRegistration(
                status="CONFLICT",
                article_id=None,
                conflict_id=conflict_id,
                matched_article_ids=candidates,
            )

        if len(candidates) == 1:
            article_id = candidates[0]
            existing_aliases = self._aliases_for_article(connection, article_id)
            if has_strong_conflict(existing_aliases, aliases):
                new_article_id = self._insert_article(
                    connection,
                    record,
                    provider=effective_provider,
                    observed_at=observed_at,
                    registry_status="identity_conflict",
                )
                aliases_added = self._attach_aliases(
                    connection,
                    new_article_id,
                    aliases,
                    observed_at=observed_at,
                )
                manifestation_added = self._insert_manifestation(
                    connection,
                    new_article_id,
                    record,
                    provider=effective_provider,
                    observed_at=observed_at,
                )
                all_candidates = tuple(sorted((article_id, new_article_id)))
                conflict_id = self._conflict(
                    connection,
                    candidate_article_ids=all_candidates,
                    aliases=aliases,
                    reason="incompatible_strong_identifiers",
                    observed_at=observed_at,
                )
                return ArticleRegistration(
                    status="CONFLICT",
                    article_id=new_article_id,
                    created=True,
                    conflict_id=conflict_id,
                    matched_article_ids=all_candidates,
                    aliases_added=aliases_added,
                    manifestation_added=manifestation_added,
                )

            changed_fields = self._update_canonical_fields(
                connection,
                article_id,
                record,
                provider=effective_provider,
                observed_at=observed_at,
            )
            aliases_added = self._attach_aliases(
                connection,
                article_id,
                aliases,
                observed_at=observed_at,
            )
            manifestation_added = self._insert_manifestation(
                connection,
                article_id,
                record,
                provider=effective_provider,
                observed_at=observed_at,
            )
            enriched = bool(changed_fields or aliases_added or manifestation_added)
            return ArticleRegistration(
                status="ENRICHED" if enriched else "MATCHED",
                article_id=article_id,
                enriched=enriched,
                matched_article_ids=(article_id,),
                aliases_added=aliases_added,
                manifestation_added=manifestation_added,
            )

        article_id = self._insert_article(
            connection,
            record,
            provider=effective_provider,
            observed_at=observed_at,
        )
        aliases_added = self._attach_aliases(
            connection,
            article_id,
            aliases,
            observed_at=observed_at,
        )
        manifestation_added = self._insert_manifestation(
            connection,
            article_id,
            record,
            provider=effective_provider,
            observed_at=observed_at,
        )
        return ArticleRegistration(
            status="CREATED",
            article_id=article_id,
            created=True,
            matched_article_ids=(article_id,),
            aliases_added=aliases_added,
            manifestation_added=manifestation_added,
        )

    def _upsert_search_run(
        self,
        connection: sqlite3.Connection,
        result: dict[str, Any],
    ) -> None:
        search_id = _text(result.get("search_id"))
        if not search_id:
            raise ValueError("search_id required for registry ingestion")
        connection.execute(
            "INSERT INTO search_runs("
            "search_id, query, search_mode, created_at, status, provider_plan_json, "
            "provider_gaps_json, search_manifest_hash"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(search_id) DO UPDATE SET "
            "query = excluded.query, search_mode = excluded.search_mode, status = excluded.status, "
            "provider_plan_json = excluded.provider_plan_json, "
            "provider_gaps_json = excluded.provider_gaps_json, "
            "search_manifest_hash = excluded.search_manifest_hash",
            (
                search_id,
                _text(result.get("query")),
                _text(result.get("search_mode")) or "interactive_bounded",
                _text(result.get("created_at")) or _now(),
                _text(result.get("status")) or "COMPLETE",
                _json(result.get("query_plan") or {}),
                _json(_provider_gaps(result)),
                _search_context_sha256(result),
            ),
        )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_search_hits_idempotent "
            "ON search_hits(search_id, article_id, provider, provider_query, reference_rank)"
        )

    def _record_hit(
        self,
        connection: sqlite3.Connection,
        *,
        result: dict[str, Any],
        row: dict[str, Any],
        article_id: str,
        provider: str,
        provider_query: str,
        retrieved_at: str,
        source_manifestation_id: str | None,
    ) -> bool:
        cursor = connection.execute(
            "INSERT OR IGNORE INTO search_hits("
            "search_id, article_id, provider, provider_query, provider_position, reference_rank, "
            "reference_score, query_relevance_score, nutev_priority_score, retrieved_at, "
            "source_manifestation_id"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                _text(result.get("search_id")),
                article_id,
                provider,
                provider_query,
                None,
                int(row.get("reference_rank") or 0) or None,
                float(row.get("reference_score") or 0.0),
                float(row.get("query_relevance_score") or 0.0),
                float(row.get("nutev_priority_score") or 0.0),
                retrieved_at or _now(),
                source_manifestation_id,
            ),
        )
        return cursor.rowcount > 0

    def ingest_search_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Attach global article IDs and durable SearchHits in one write transaction."""

        if not isinstance(result, dict):
            raise TypeError("search result must be a dict")
        search_id = _text(result.get("search_id"))
        if not search_id:
            raise ValueError("search result has no search_id")
        rows = result.get("results")
        if rows is None:
            rows = []
        if not isinstance(rows, list):
            raise ValueError("search result results must be a list")

        before = self.stats().articles
        counts: Counter[str] = Counter()
        hits_recorded = 0
        observed = _text(result.get("created_at")) or _now()

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._upsert_search_run(connection, result)

            for raw_row in rows:
                if not isinstance(raw_row, dict):
                    counts["UNRESOLVED"] += 1
                    continue
                stable = _stable_record(raw_row)
                try:
                    registration = self._register_one(
                        connection,
                        stable,
                        provider=_provider_name(stable),
                        observed_at=observed,
                    )
                except (TypeError, ValueError):
                    raw_row["article_id"] = None
                    raw_row["registry_identity_status"] = "UNRESOLVED"
                    counts["UNRESOLVED"] += 1
                    continue

                counts[registration.status] += 1
                raw_row["article_id"] = registration.article_id
                raw_row["registry_identity_status"] = registration.status
                if registration.conflict_id:
                    raw_row["registry_conflict_id"] = registration.conflict_id
                else:
                    raw_row.pop("registry_conflict_id", None)

                article_id = registration.article_id
                if not article_id:
                    continue

                manifestations = _manifestation_rows(stable)
                hit_rows: list[tuple[str, str, str, str | None]] = []
                if manifestations:
                    for manifestation in manifestations:
                        provider = _provider_name(manifestation, _provider_name(stable))
                        provider_query = _text(
                            manifestation.get("provider_query") or stable.get("provider_query")
                        )
                        retrieved_at = _text(
                            manifestation.get("interactive_retrieved_at")
                            or manifestation.get("retrieved_at")
                            or stable.get("interactive_retrieved_at")
                        ) or observed
                        aliases = observed_aliases(manifestation, provider=provider)
                        exact_aliases = [
                            alias for alias in aliases if alias.scheme != "metadata_fingerprint"
                        ]
                        manifestation_id: str | None = None
                        if exact_aliases:
                            manifest_registration = self._register_one(
                                connection,
                                manifestation,
                                provider=provider,
                                observed_at=retrieved_at,
                            )
                            if manifest_registration.article_id == article_id:
                                candidate_id = _manifestation_id(article_id, manifestation, provider)
                                exists = connection.execute(
                                    "SELECT 1 FROM article_manifestations WHERE manifestation_id = ?",
                                    (candidate_id,),
                                ).fetchone()
                                manifestation_id = candidate_id if exists else None
                        hit_rows.append(
                            (provider, provider_query, retrieved_at, manifestation_id)
                        )
                else:
                    provider = _provider_name(stable)
                    provider_query = _text(stable.get("provider_query"))
                    retrieved_at = _text(
                        stable.get("interactive_retrieved_at") or stable.get("retrieved_at")
                    ) or observed
                    candidate_id = _manifestation_id(article_id, stable, provider)
                    exists = connection.execute(
                        "SELECT 1 FROM article_manifestations WHERE manifestation_id = ?",
                        (candidate_id,),
                    ).fetchone()
                    hit_rows.append(
                        (provider, provider_query, retrieved_at, candidate_id if exists else None)
                    )

                seen_hits: set[tuple[str, str]] = set()
                for provider, provider_query, retrieved_at, manifestation_id in hit_rows:
                    hit_key = (provider, provider_query)
                    if hit_key in seen_hits:
                        continue
                    seen_hits.add(hit_key)
                    if self._record_hit(
                        connection,
                        result=result,
                        row=raw_row,
                        article_id=article_id,
                        provider=provider,
                        provider_query=provider_query,
                        retrieved_at=retrieved_at,
                        source_manifestation_id=manifestation_id,
                    ):
                        hits_recorded += 1

        self._write_manifest()
        after = self.stats().articles
        conflicts = int(counts.get("CONFLICT", 0))
        unresolved = int(counts.get("UNRESOLVED", 0))
        summary = {
            "status": "COMPLETE_WITH_IDENTITY_GAPS" if (conflicts or unresolved) else "COMPLETE",
            "search_id": search_id,
            "registry_created": int(counts.get("CREATED", 0)),
            "registry_matches": int(counts.get("MATCHED", 0) + counts.get("ENRICHED", 0)),
            "registry_enriched": int(counts.get("ENRICHED", 0)),
            "registry_conflicts": conflicts,
            "registry_unresolved": unresolved,
            "search_hits_recorded": hits_recorded,
            "articles_before": before,
            "articles_after": after,
            "article_count_delta": after - before,
            "registry_total_articles": after,
            "registry_integrity": self.integrity_check(),
            "semantics": "discovery/indexing provenance only; not scientific inclusion or PRISMA",
        }
        result["registry_summary"] = summary
        return summary


def register_search_result(
    result: dict[str, Any],
    *,
    output_root: Path,
) -> dict[str, Any]:
    registry_root = Path(output_root) / "registry"
    registry = SearchRegistryIngestor(
        registry_root / "article_registry.sqlite",
        registry_root / "ARTICLE_REGISTRY_MANIFEST.json",
    )
    registry.ingest_search_result(result)
    return result
