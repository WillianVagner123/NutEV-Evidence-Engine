from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable
from uuid import uuid4

from .identity import has_strong_conflict, observed_aliases
from .migrations import SCHEMA_VERSION, apply_migrations
from .models import ArticleRegistration, RegistryAlias, RegistryStats


def _now(value: str | None = None) -> str:
    return str(value or datetime.now(timezone.utc).isoformat())


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _year(value: Any) -> int | None:
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year if 1000 <= year <= 3000 else None


def _payload_hash(record: dict[str, Any]) -> str:
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _provider_name(record: dict[str, Any], fallback: str = "") -> str:
    return _text(
        record.get("source_provider")
        or record.get("provider")
        or record.get("source")
        or fallback
    )


def _provider_record_id(record: dict[str, Any]) -> str:
    for key in (
        "provider_record_id",
        "pmid",
        "doi",
        "pmcid",
        "openalex_id",
        "semantic_scholar_id",
        "crossref_id",
        "id",
    ):
        value = _text(record.get(key))
        if value:
            return value
    return ""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


class SQLiteArticleRegistry:
    """Durable, cumulative article identity registry backed by SQLite."""

    def __init__(self, database_path: Path, manifest_path: Path | None = None) -> None:
        self._database_path = Path(database_path)
        self._manifest_path = manifest_path or self._database_path.with_name(
            "ARTICLE_REGISTRY_MANIFEST.json"
        )
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @property
    def database_path(self) -> Path:
        return self._database_path

    @property
    def manifest_path(self) -> Path:
        return self._manifest_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            apply_migrations(connection)
        self._write_manifest()

    def _candidate_article_ids(
        self,
        connection: sqlite3.Connection,
        aliases: Iterable[RegistryAlias],
    ) -> tuple[str, ...]:
        article_ids: set[str] = set()
        for alias in aliases:
            row = connection.execute(
                "SELECT article_id FROM article_aliases WHERE scheme = ? AND normalized_value = ?",
                (alias.scheme, alias.normalized_value),
            ).fetchone()
            if row:
                article_ids.add(str(row["article_id"]))
        return tuple(sorted(article_ids))

    def _aliases_for_article(
        self,
        connection: sqlite3.Connection,
        article_id: str,
    ) -> tuple[RegistryAlias, ...]:
        rows = connection.execute(
            "SELECT scheme, normalized_value, raw_value, provider "
            "FROM article_aliases WHERE article_id = ? ORDER BY scheme, normalized_value",
            (article_id,),
        ).fetchall()
        return tuple(
            RegistryAlias(
                scheme=str(row["scheme"]),
                normalized_value=str(row["normalized_value"]),
                raw_value=str(row["raw_value"] or ""),
                provider=str(row["provider"] or ""),
            )
            for row in rows
        )

    def _record_field_history(
        self,
        connection: sqlite3.Connection,
        *,
        article_id: str,
        field_name: str,
        value: Any,
        provider: str,
        observed_at: str,
        precedence_rule: str,
        source_payload_hash: str,
    ) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO article_field_history("
            "article_id, field_name, value_json, provider, observed_at, precedence_rule, "
            "source_payload_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                article_id,
                field_name,
                _json(value),
                provider,
                observed_at,
                precedence_rule,
                source_payload_hash,
            ),
        )

    def _insert_article(
        self,
        connection: sqlite3.Connection,
        record: dict[str, Any],
        *,
        provider: str,
        observed_at: str,
        registry_status: str = "active",
    ) -> str:
        article_id = "NUTEV-ART-" + uuid4().hex[:16]
        title = _text(record.get("title"))
        publication_year = _year(record.get("year") or record.get("publication_year"))
        journal = _text(record.get("journal") or record.get("venue"))
        abstract = _text(record.get("abstract") or record.get("summary"))
        connection.execute(
            "INSERT INTO articles("
            "article_id, canonical_title, publication_year, journal, abstract, created_at, "
            "updated_at, first_seen_at, last_seen_at, registry_status"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                article_id,
                title,
                publication_year,
                journal,
                abstract,
                observed_at,
                observed_at,
                observed_at,
                observed_at,
                registry_status,
            ),
        )
        source_hash = _payload_hash(record)
        for field_name, value in (
            ("canonical_title", title),
            ("publication_year", publication_year),
            ("journal", journal),
            ("abstract", abstract),
        ):
            if value not in (None, ""):
                self._record_field_history(
                    connection,
                    article_id=article_id,
                    field_name=field_name,
                    value=value,
                    provider=provider,
                    observed_at=observed_at,
                    precedence_rule="first_observed",
                    source_payload_hash=source_hash,
                )
        return article_id

    def _attach_aliases(
        self,
        connection: sqlite3.Connection,
        article_id: str,
        aliases: Iterable[RegistryAlias],
        *,
        observed_at: str,
    ) -> int:
        added = 0
        for alias in aliases:
            owner = connection.execute(
                "SELECT article_id FROM article_aliases WHERE scheme = ? AND normalized_value = ?",
                (alias.scheme, alias.normalized_value),
            ).fetchone()
            if owner and str(owner["article_id"]) != article_id:
                continue
            if owner:
                connection.execute(
                    "UPDATE article_aliases SET last_seen_at = ? WHERE scheme = ? AND normalized_value = ?",
                    (observed_at, alias.scheme, alias.normalized_value),
                )
                continue
            connection.execute(
                "INSERT INTO article_aliases("
                "article_id, scheme, normalized_value, raw_value, provider, first_seen_at, last_seen_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    article_id,
                    alias.scheme,
                    alias.normalized_value,
                    alias.raw_value,
                    alias.provider,
                    observed_at,
                    observed_at,
                ),
            )
            added += 1
        return added

    def _update_canonical_fields(
        self,
        connection: sqlite3.Connection,
        article_id: str,
        record: dict[str, Any],
        *,
        provider: str,
        observed_at: str,
    ) -> bool:
        current = connection.execute(
            "SELECT canonical_title, publication_year, journal, abstract FROM articles WHERE article_id = ?",
            (article_id,),
        ).fetchone()
        if current is None:
            raise KeyError(article_id)

        incoming = {
            "canonical_title": _text(record.get("title")),
            "publication_year": _year(record.get("year") or record.get("publication_year")),
            "journal": _text(record.get("journal") or record.get("venue")),
            "abstract": _text(record.get("abstract") or record.get("summary")),
        }
        updates: dict[str, Any] = {}
        rules: dict[str, str] = {}
        for field_name in ("canonical_title", "publication_year", "journal"):
            if current[field_name] in (None, "") and incoming[field_name] not in (None, ""):
                updates[field_name] = incoming[field_name]
                rules[field_name] = "fill_missing_canonical"
        if incoming["abstract"] and len(str(incoming["abstract"])) > len(str(current["abstract"] or "")):
            updates["abstract"] = incoming["abstract"]
            rules["abstract"] = "prefer_longer_observed_abstract"

        if updates:
            assignments = ", ".join(f"{field_name} = ?" for field_name in updates)
            connection.execute(
                f"UPDATE articles SET {assignments}, updated_at = ?, last_seen_at = ? WHERE article_id = ?",
                (*updates.values(), observed_at, observed_at, article_id),
            )
            source_hash = _payload_hash(record)
            for field_name, value in updates.items():
                self._record_field_history(
                    connection,
                    article_id=article_id,
                    field_name=field_name,
                    value=value,
                    provider=provider,
                    observed_at=observed_at,
                    precedence_rule=rules[field_name],
                    source_payload_hash=source_hash,
                )
        else:
            connection.execute(
                "UPDATE articles SET last_seen_at = ? WHERE article_id = ?",
                (observed_at, article_id),
            )
        return bool(updates)

    def _insert_manifestation(
        self,
        connection: sqlite3.Connection,
        article_id: str,
        record: dict[str, Any],
        *,
        provider: str,
        observed_at: str,
    ) -> bool:
        source_hash = _payload_hash(record)
        provider_record_id = _provider_record_id(record)
        identity_seed = f"{article_id}|{provider}|{provider_record_id}|{source_hash}"
        manifestation_id = "NUTEV-MAN-" + sha256(identity_seed.encode("utf-8")).hexdigest()[:24]
        identifiers = {
            key: record.get(key)
            for key in (
                "doi",
                "pmid",
                "pmcid",
                "openalex_id",
                "semantic_scholar_id",
                "crossref_id",
                "url",
            )
            if record.get(key) not in (None, "")
        }
        cursor = connection.execute(
            "INSERT OR IGNORE INTO article_manifestations("
            "manifestation_id, article_id, provider, provider_record_id, title, abstract, "
            "authors_json, journal, publication_year, raw_identifiers_json, retrieved_at, "
            "source_payload_hash, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                manifestation_id,
                article_id,
                provider,
                provider_record_id,
                _text(record.get("title")),
                _text(record.get("abstract") or record.get("summary")),
                _json(record.get("authors") or []),
                _text(record.get("journal") or record.get("venue")),
                _year(record.get("year") or record.get("publication_year")),
                _json(identifiers),
                _text(record.get("interactive_retrieved_at") or record.get("retrieved_at"))
                or observed_at,
                source_hash,
                observed_at,
            ),
        )
        return cursor.rowcount > 0

    def _conflict(
        self,
        connection: sqlite3.Connection,
        *,
        candidate_article_ids: Iterable[str],
        aliases: Iterable[RegistryAlias],
        reason: str,
        observed_at: str,
    ) -> str:
        article_ids = tuple(sorted(set(candidate_article_ids)))
        identifiers = tuple(sorted((alias.scheme, alias.normalized_value) for alias in aliases))
        payload = _json(
            {
                "candidate_article_ids": article_ids,
                "identifiers": identifiers,
                "reason": reason,
            }
        )
        fingerprint = sha256(payload.encode("utf-8")).hexdigest()
        conflict_id = "NUTEV-CONFLICT-" + fingerprint[:20]
        connection.execute(
            "INSERT INTO identity_conflicts("
            "conflict_id, fingerprint, candidate_article_ids_json, identifiers_json, reason, "
            "status, created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, 'open', ?, ?) "
            "ON CONFLICT(fingerprint) DO UPDATE SET updated_at = excluded.updated_at",
            (
                conflict_id,
                fingerprint,
                _json(article_ids),
                _json(identifiers),
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

    def register_article(
        self,
        record: dict[str, Any],
        *,
        provider: str = "",
        observed_at: str | None = None,
    ) -> ArticleRegistration:
        """Create, match, enrich, or quarantine one observed article manifestation."""

        if not isinstance(record, dict):
            raise TypeError("record must be a dict")
        observed = _now(observed_at)
        effective_provider = _provider_name(record, provider)
        aliases = observed_aliases(record, provider=effective_provider)
        if not aliases:
            raise ValueError("article identity unavailable: title or exact alias required")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            candidates = self._candidate_article_ids(connection, aliases)

            if len(candidates) > 1:
                conflict_id = self._conflict(
                    connection,
                    candidate_article_ids=candidates,
                    aliases=aliases,
                    reason="observed_aliases_resolve_multiple_articles",
                    observed_at=observed,
                )
                result = ArticleRegistration(
                    status="CONFLICT",
                    article_id=None,
                    conflict_id=conflict_id,
                    matched_article_ids=candidates,
                )
            elif len(candidates) == 1:
                article_id = candidates[0]
                existing_aliases = self._aliases_for_article(connection, article_id)
                if has_strong_conflict(existing_aliases, aliases):
                    new_article_id = self._insert_article(
                        connection,
                        record,
                        provider=effective_provider,
                        observed_at=observed,
                        registry_status="identity_conflict",
                    )
                    aliases_added = self._attach_aliases(
                        connection,
                        new_article_id,
                        aliases,
                        observed_at=observed,
                    )
                    manifestation_added = self._insert_manifestation(
                        connection,
                        new_article_id,
                        record,
                        provider=effective_provider,
                        observed_at=observed,
                    )
                    all_candidates = tuple(sorted((article_id, new_article_id)))
                    conflict_id = self._conflict(
                        connection,
                        candidate_article_ids=all_candidates,
                        aliases=aliases,
                        reason="incompatible_strong_identifiers",
                        observed_at=observed,
                    )
                    result = ArticleRegistration(
                        status="CONFLICT",
                        article_id=new_article_id,
                        created=True,
                        conflict_id=conflict_id,
                        matched_article_ids=all_candidates,
                        aliases_added=aliases_added,
                        manifestation_added=manifestation_added,
                    )
                else:
                    changed_fields = self._update_canonical_fields(
                        connection,
                        article_id,
                        record,
                        provider=effective_provider,
                        observed_at=observed,
                    )
                    aliases_added = self._attach_aliases(
                        connection,
                        article_id,
                        aliases,
                        observed_at=observed,
                    )
                    manifestation_added = self._insert_manifestation(
                        connection,
                        article_id,
                        record,
                        provider=effective_provider,
                        observed_at=observed,
                    )
                    enriched = bool(changed_fields or aliases_added or manifestation_added)
                    result = ArticleRegistration(
                        status="ENRICHED" if enriched else "MATCHED",
                        article_id=article_id,
                        enriched=enriched,
                        matched_article_ids=(article_id,),
                        aliases_added=aliases_added,
                        manifestation_added=manifestation_added,
                    )
            else:
                article_id = self._insert_article(
                    connection,
                    record,
                    provider=effective_provider,
                    observed_at=observed,
                )
                aliases_added = self._attach_aliases(
                    connection,
                    article_id,
                    aliases,
                    observed_at=observed,
                )
                manifestation_added = self._insert_manifestation(
                    connection,
                    article_id,
                    record,
                    provider=effective_provider,
                    observed_at=observed,
                )
                result = ArticleRegistration(
                    status="CREATED",
                    article_id=article_id,
                    created=True,
                    matched_article_ids=(article_id,),
                    aliases_added=aliases_added,
                    manifestation_added=manifestation_added,
                )

        self._write_manifest()
        return result

    def get_article(self, article_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            article = connection.execute(
                "SELECT * FROM articles WHERE article_id = ?",
                (article_id,),
            ).fetchone()
            if article is None:
                return None
            aliases = connection.execute(
                "SELECT scheme, normalized_value, raw_value, provider, first_seen_at, last_seen_at "
                "FROM article_aliases WHERE article_id = ? ORDER BY scheme, normalized_value",
                (article_id,),
            ).fetchall()
            manifestation_count = connection.execute(
                "SELECT COUNT(*) FROM article_manifestations WHERE article_id = ?",
                (article_id,),
            ).fetchone()[0]
        payload = dict(article)
        payload["aliases"] = [dict(row) for row in aliases]
        payload["manifestation_count"] = int(manifestation_count)
        return payload

    def stats(self) -> RegistryStats:
        with self._connect() as connection:
            def count(table: str, where: str = "") -> int:
                return int(connection.execute(f"SELECT COUNT(*) FROM {table}{where}").fetchone()[0])

            return RegistryStats(
                articles=count("articles"),
                aliases=count("article_aliases"),
                manifestations=count("article_manifestations"),
                search_runs=count("search_runs"),
                search_hits=count("search_hits"),
                identity_conflicts_open=count("identity_conflicts", " WHERE status = 'open'"),
            )

    def integrity_check(self) -> str:
        with self._connect() as connection:
            row = connection.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else "missing_result"

    def _write_manifest(self) -> None:
        integrity = self.integrity_check()
        stats = self.stats()
        database_sha = sha256(self._database_path.read_bytes()).hexdigest()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "registry_type": "NUTEV_CUMULATIVE_ARTICLE_REGISTRY",
            "status": "PASS" if integrity == "ok" else "FAIL",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database": {
                "path": str(self._database_path),
                "sha256": database_sha,
                "integrity_check": integrity,
            },
            "counts": {
                "articles": stats.articles,
                "aliases": stats.aliases,
                "manifestations": stats.manifestations,
                "search_runs": stats.search_runs,
                "search_hits": stats.search_hits,
                "identity_conflicts_open": stats.identity_conflicts_open,
            },
            "guardrails": {
                "one_article_owns_global_identity": True,
                "search_rank_is_contextual_not_article_quality": True,
                "registry_presence_is_not_scientific_inclusion": True,
                "registry_presence_is_not_prisma_event": True,
                "fuzzy_identity_merge": False,
            },
        }
        self._manifest_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._manifest_path.with_name(f".{self._manifest_path.name}.{uuid4().hex}.tmp")
        tmp.write_text(_json(payload) + "\n", encoding="utf-8")
        tmp.replace(self._manifest_path)
