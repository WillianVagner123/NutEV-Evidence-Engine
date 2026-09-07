from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
from typing import Any, Mapping
from uuid import uuid4

from nutev.reference_identity import normalize_doi, normalize_pmid

from .sqlite_store import SQLiteArticleRegistry


WORKBENCH_SCHEMA = "NUTEV_ARTICLE_WORKBENCH_V1"


class RegistryWorkbenchError(RuntimeError):
    """Raised when the cumulative Registry projection cannot be proven safe."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryWorkbenchError(f"invalid Workbench manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryWorkbenchError("Workbench manifest must be an object")
    return value


def _resolve_existing_database(workbench_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    manifest_path = workbench_root / "WORKBENCH_MANIFEST.json"
    database_path = workbench_root / "evidence_workbench.sqlite"
    if not manifest_path.exists() and not database_path.exists():
        return None, None
    if not manifest_path.is_file():
        raise RegistryWorkbenchError("existing Workbench database has no verified manifest")
    manifest = _read_json(manifest_path)
    if manifest.get("workbench_type") != WORKBENCH_SCHEMA or manifest.get("status") != "PASS":
        raise RegistryWorkbenchError("existing Workbench manifest is not a passing NutEV Workbench")
    output = (manifest.get("outputs") or {}).get("database") or {}
    raw_path = str(output.get("path") or "").strip()
    source = Path(raw_path) if raw_path else database_path
    if not source.is_absolute():
        candidate = (Path.cwd() / source).resolve()
        source = candidate if candidate.is_file() else database_path
    expected = str(output.get("sha256") or "").strip().lower()
    if not source.is_file() or not expected:
        raise RegistryWorkbenchError("existing Workbench database or SHA-256 is missing")
    actual = _sha256_file(source)
    if actual != expected:
        raise RegistryWorkbenchError(
            f"existing Workbench SHA-256 mismatch: expected {expected}, got {actual}"
        )
    with sqlite3.connect(source) as connection:
        row = connection.execute("PRAGMA integrity_check").fetchone()
    if not row or row[0] != "ok":
        raise RegistryWorkbenchError("existing Workbench integrity_check failed")
    return source, manifest


def _create_base_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS article_cards (
            document_id TEXT PRIMARY KEY,
            record_id TEXT,
            title TEXT,
            year INTEGER,
            doi TEXT,
            pmid TEXT,
            source_provider TEXT,
            document_class TEXT,
            full_text_status TEXT,
            cache_key TEXT NOT NULL,
            reference_stub TEXT,
            llm_context_chars INTEGER NOT NULL DEFAULT 0,
            search_text TEXT NOT NULL,
            card_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_article_year ON article_cards(year DESC);
        CREATE INDEX IF NOT EXISTS idx_article_provider ON article_cards(source_provider);
        CREATE INDEX IF NOT EXISTS idx_article_class ON article_cards(document_class);
        CREATE INDEX IF NOT EXISTS idx_article_full_text ON article_cards(full_text_status);
        CREATE INDEX IF NOT EXISTS idx_article_doi ON article_cards(doi);
        CREATE INDEX IF NOT EXISTS idx_article_pmid ON article_cards(pmid);

        CREATE TABLE IF NOT EXISTS evidence_excerpts (
            excerpt_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            section TEXT,
            locator TEXT,
            priority_score REAL NOT NULL,
            verbatim_excerpt TEXT NOT NULL,
            excerpt_json TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES article_cards(document_id)
        );
        CREATE INDEX IF NOT EXISTS idx_excerpt_document ON evidence_excerpts(document_id);
        CREATE INDEX IF NOT EXISTS idx_excerpt_kind ON evidence_excerpts(kind);

        CREATE TABLE IF NOT EXISTS result_bundles (
            result_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            result_kind TEXT NOT NULL,
            priority_score REAL NOT NULL,
            result_json TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES article_cards(document_id)
        );
        CREATE INDEX IF NOT EXISTS idx_result_document ON result_bundles(document_id);
        CREATE INDEX IF NOT EXISTS idx_result_kind ON result_bundles(result_kind);

        CREATE TABLE IF NOT EXISTS workbench_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )


def _ensure_registry_columns(connection: sqlite3.Connection) -> None:
    columns = {
        str(row[1])
        for row in connection.execute("PRAGMA table_info(article_cards)").fetchall()
    }
    additions = {
        "article_id": "TEXT",
        "registry_scope": "TEXT NOT NULL DEFAULT 'legacy_scientific'",
        "registry_status": "TEXT",
    }
    for name, ddl in additions.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE article_cards ADD COLUMN {name} {ddl}")
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_article_registry_id ON article_cards(article_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_article_registry_scope ON article_cards(registry_scope)"
    )


def _registry_rows(registry_db: Path) -> list[dict[str, Any]]:
    connection = sqlite3.connect(registry_db)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT article_id, canonical_title, publication_year, journal, abstract, "
            "first_seen_at, last_seen_at, registry_status FROM articles ORDER BY article_id"
        ).fetchall()
        aliases = connection.execute(
            "SELECT article_id, scheme, normalized_value, provider "
            "FROM article_aliases ORDER BY article_id, scheme, normalized_value"
        ).fetchall()
        manifestations = connection.execute(
            "SELECT article_id, provider, authors_json, retrieved_at FROM article_manifestations "
            "ORDER BY article_id, retrieved_at DESC"
        ).fetchall()
        hits = connection.execute(
            "SELECT article_id, COUNT(*) AS hit_count, COUNT(DISTINCT search_id) AS search_count, "
            "COUNT(DISTINCT provider) AS provider_count FROM search_hits GROUP BY article_id"
        ).fetchall()
    finally:
        connection.close()

    alias_map: dict[str, list[dict[str, str]]] = {}
    for row in aliases:
        alias_map.setdefault(str(row["article_id"]), []).append(dict(row))
    manifestation_map: dict[str, dict[str, Any]] = {}
    for row in manifestations:
        manifestation_map.setdefault(str(row["article_id"]), dict(row))
    hit_map = {str(row["article_id"]): dict(row) for row in hits}

    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        article_id = str(item["article_id"])
        item["aliases"] = alias_map.get(article_id, [])
        item["latest_manifestation"] = manifestation_map.get(article_id, {})
        item["hit_stats"] = hit_map.get(
            article_id,
            {"hit_count": 0, "search_count": 0, "provider_count": 0},
        )
        output.append(item)
    return output


def _alias_value(article: Mapping[str, Any], scheme: str) -> str:
    for alias in article.get("aliases") or []:
        if str(alias.get("scheme") or "") == scheme:
            return str(alias.get("normalized_value") or "")
    return ""


def _existing_identity_maps(connection: sqlite3.Connection) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, str]]:
    doi_map: dict[str, list[str]] = {}
    pmid_map: dict[str, list[str]] = {}
    article_id_map: dict[str, str] = {}
    columns = {
        str(row[1])
        for row in connection.execute("PRAGMA table_info(article_cards)").fetchall()
    }
    article_select = "article_id" if "article_id" in columns else "NULL AS article_id"
    rows = connection.execute(
        f"SELECT document_id, doi, pmid, {article_select} FROM article_cards"
    ).fetchall()
    for row in rows:
        document_id = str(row[0])
        doi = normalize_doi(row[1])
        pmid = normalize_pmid(row[2])
        article_id = str(row[3] or "")
        if doi:
            doi_map.setdefault(doi, []).append(document_id)
        if pmid:
            pmid_map.setdefault(pmid, []).append(document_id)
        if article_id:
            article_id_map[article_id] = document_id
    return doi_map, pmid_map, article_id_map


def _candidate_documents(
    article: Mapping[str, Any],
    doi_map: Mapping[str, list[str]],
    pmid_map: Mapping[str, list[str]],
    article_id_map: Mapping[str, str],
) -> set[str]:
    article_id = str(article.get("article_id") or "")
    if article_id in article_id_map:
        return {article_id_map[article_id]}
    candidates: set[str] = set()
    doi = normalize_doi(_alias_value(article, "doi"))
    pmid = normalize_pmid(_alias_value(article, "pmid"))
    if doi:
        candidates.update(doi_map.get(doi, []))
    if pmid:
        candidates.update(pmid_map.get(pmid, []))
    return candidates


def _authors(article: Mapping[str, Any]) -> list[Any]:
    raw = (article.get("latest_manifestation") or {}).get("authors_json")
    if not raw:
        return []
    try:
        value = json.loads(str(raw))
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _provider(article: Mapping[str, Any]) -> str:
    manifestation = article.get("latest_manifestation") or {}
    provider = str(manifestation.get("provider") or "").strip()
    if provider:
        return provider
    for alias in article.get("aliases") or []:
        provider = str(alias.get("provider") or "").strip()
        if provider:
            return provider
    return "registry"


def _reference_stub(article: Mapping[str, Any]) -> str:
    parts = [str(article.get("canonical_title") or "").strip()]
    journal = str(article.get("journal") or "").strip()
    year = article.get("publication_year")
    if journal:
        parts.append(journal)
    if year:
        parts.append(str(year))
    return ". ".join(part for part in parts if part)


def _search_text(article: Mapping[str, Any]) -> str:
    aliases = " ".join(
        str(alias.get("normalized_value") or "") for alias in article.get("aliases") or []
    )
    authors = " ".join(str(author) for author in _authors(article))
    text = " ".join(
        [
            str(article.get("canonical_title") or ""),
            str(article.get("journal") or ""),
            str(article.get("abstract") or ""),
            aliases,
            authors,
            _provider(article),
        ]
    )
    return " ".join(text.casefold().split())[:20000]


def _registry_card(article: Mapping[str, Any], *, document_id: str) -> dict[str, Any]:
    article_id = str(article.get("article_id") or "")
    doi = _alias_value(article, "doi")
    pmid = _alias_value(article, "pmid")
    hits = article.get("hit_stats") or {}
    return {
        "document_id": document_id,
        "article_id": article_id,
        "record_id": None,
        "identity": {
            "title": article.get("canonical_title"),
            "doi": doi or None,
            "pmid": pmid or None,
            "year": article.get("publication_year"),
            "source_provider": _provider(article),
        },
        "reference": {
            "authors": _authors(article),
            "journal": article.get("journal"),
            "reference_stub": _reference_stub(article),
        },
        "study_snapshot": {},
        "document_class": "unclassified",
        "full_text_status": "registry_metadata_only",
        "cache_key": f"registry:{article_id}",
        "llm_context_chars": 0,
        "registry": {
            "status": article.get("registry_status"),
            "scope": "global_article_registry",
            "first_seen_at": article.get("first_seen_at"),
            "last_seen_at": article.get("last_seen_at"),
            "search_hits": int(hits.get("hit_count") or 0),
            "searches": int(hits.get("search_count") or 0),
            "providers": int(hits.get("provider_count") or 0),
            "semantics": "discovery/indexing only; not scientific inclusion or quality",
        },
    }


def _merge_registry_into_card(raw_card: str, article: Mapping[str, Any], *, document_id: str) -> str:
    try:
        card = json.loads(raw_card)
    except json.JSONDecodeError:
        card = {}
    if not isinstance(card, dict):
        card = {}
    registry_card = _registry_card(article, document_id=document_id)
    card["article_id"] = registry_card["article_id"]
    card["registry"] = registry_card["registry"]
    identity = card.setdefault("identity", {})
    if isinstance(identity, dict):
        for key, value in registry_card["identity"].items():
            if identity.get(key) in (None, "") and value not in (None, ""):
                identity[key] = value
    reference = card.setdefault("reference", {})
    if isinstance(reference, dict):
        for key, value in registry_card["reference"].items():
            if reference.get(key) in (None, "", []) and value not in (None, "", []):
                reference[key] = value
    return json.dumps(card, ensure_ascii=False, sort_keys=True, default=str)


def _link_existing(
    connection: sqlite3.Connection,
    document_id: str,
    article: Mapping[str, Any],
) -> None:
    current = connection.execute(
        "SELECT title, year, doi, pmid, source_provider, search_text, card_json "
        "FROM article_cards WHERE document_id = ?",
        (document_id,),
    ).fetchone()
    if current is None:
        raise RegistryWorkbenchError(f"legacy Workbench row disappeared: {document_id}")
    doi = _alias_value(article, "doi")
    pmid = _alias_value(article, "pmid")
    merged_search = " ".join(
        (str(current[5] or "") + " " + _search_text(article)).split()
    )[:20000]
    connection.execute(
        "UPDATE article_cards SET article_id = ?, registry_scope = 'registry_linked', "
        "registry_status = ?, title = CASE WHEN COALESCE(title, '') = '' THEN ? ELSE title END, "
        "year = COALESCE(year, ?), doi = CASE WHEN COALESCE(doi, '') = '' THEN ? ELSE doi END, "
        "pmid = CASE WHEN COALESCE(pmid, '') = '' THEN ? ELSE pmid END, "
        "source_provider = CASE WHEN COALESCE(source_provider, '') = '' THEN ? ELSE source_provider END, "
        "search_text = ?, card_json = ? WHERE document_id = ?",
        (
            article.get("article_id"),
            article.get("registry_status"),
            article.get("canonical_title"),
            article.get("publication_year"),
            doi or None,
            pmid or None,
            _provider(article),
            merged_search,
            _merge_registry_into_card(str(current[6]), article, document_id=document_id),
            document_id,
        ),
    )


def _insert_registry_only(connection: sqlite3.Connection, article: Mapping[str, Any]) -> None:
    article_id = str(article.get("article_id") or "")
    card = _registry_card(article, document_id=article_id)
    connection.execute(
        "INSERT OR IGNORE INTO article_cards("
        "document_id, record_id, title, year, doi, pmid, source_provider, document_class, "
        "full_text_status, cache_key, reference_stub, llm_context_chars, search_text, card_json, "
        "article_id, registry_scope, registry_status"
        ") VALUES (?, NULL, ?, ?, ?, ?, ?, 'unclassified', 'registry_metadata_only', ?, ?, 0, ?, ?, ?, ?, ?)",
        (
            article_id,
            article.get("canonical_title"),
            article.get("publication_year"),
            _alias_value(article, "doi") or None,
            _alias_value(article, "pmid") or None,
            _provider(article),
            f"registry:{article_id}",
            _reference_stub(article),
            _search_text(article),
            json.dumps(card, ensure_ascii=False, sort_keys=True, default=str),
            article_id,
            "registry_only",
            article.get("registry_status"),
        ),
    )


def refresh_cumulative_workbench(
    *,
    output_root: Path,
) -> dict[str, Any]:
    """Atomically project the cumulative Article Registry into Article Workbench.

    Existing scientific cards/excerpts/bundles are copied first and never deleted.
    Exact DOI/PMID matches are linked to durable article IDs. Registry articles that
    are not yet scientifically materialized enter as metadata-only cards.
    """

    root = Path(output_root).resolve()
    registry_db = root / "registry" / "article_registry.sqlite"
    if not registry_db.is_file():
        raise RegistryWorkbenchError("Article Registry database is missing")
    registry = SQLiteArticleRegistry(
        registry_db,
        root / "registry" / "ARTICLE_REGISTRY_MANIFEST.json",
    )
    if registry.integrity_check() != "ok":
        raise RegistryWorkbenchError("Article Registry integrity_check failed")

    registry_sha = _sha256_file(registry_db)
    registry_articles = _registry_rows(registry_db)
    workbench_root = root / "scientific" / "workbench"
    workbench_root.mkdir(parents=True, exist_ok=True)
    active_db = workbench_root / "evidence_workbench.sqlite"
    existing_db, existing_manifest = _resolve_existing_database(workbench_root)
    temp_db = workbench_root / f".evidence_workbench.sqlite.{uuid4().hex}.tmp"

    if existing_db is not None:
        shutil.copy2(existing_db, temp_db)
    else:
        with sqlite3.connect(temp_db) as connection:
            _create_base_schema(connection)
            connection.commit()

    linked_existing = 0
    inserted_registry_only = 0
    legacy_identity_ambiguities = 0
    try:
        connection = sqlite3.connect(temp_db)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            _create_base_schema(connection)
            _ensure_registry_columns(connection)
            before_count = int(connection.execute("SELECT COUNT(*) FROM article_cards").fetchone()[0])
            doi_map, pmid_map, article_id_map = _existing_identity_maps(connection)

            for article in registry_articles:
                candidates = _candidate_documents(article, doi_map, pmid_map, article_id_map)
                if len(candidates) == 1:
                    document_id = next(iter(candidates))
                    _link_existing(connection, document_id, article)
                    article_id_map[str(article["article_id"])] = document_id
                    linked_existing += 1
                else:
                    if len(candidates) > 1:
                        legacy_identity_ambiguities += 1
                    before = connection.total_changes
                    _insert_registry_only(connection, article)
                    if connection.total_changes > before:
                        inserted_registry_only += 1
                    article_id_map[str(article["article_id"])] = str(article["article_id"])

            connection.execute(
                "INSERT INTO workbench_meta(key, value) VALUES('schema', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (WORKBENCH_SCHEMA,),
            )
            connection.execute(
                "INSERT INTO workbench_meta(key, value) VALUES('article_registry_sha256', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (registry_sha,),
            )
            connection.execute(
                "INSERT INTO workbench_meta(key, value) VALUES('registry_projection_at', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (_now(),),
            )
            connection.commit()
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise RegistryWorkbenchError("cumulative Workbench integrity_check failed")
            after_count = int(connection.execute("SELECT COUNT(*) FROM article_cards").fetchone()[0])
            excerpt_count = int(connection.execute("SELECT COUNT(*) FROM evidence_excerpts").fetchone()[0])
            bundle_count = int(connection.execute("SELECT COUNT(*) FROM result_bundles").fetchone()[0])
            linked_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM article_cards WHERE COALESCE(article_id, '') <> ''"
                ).fetchone()[0]
            )
            legacy_preserved = int(
                connection.execute(
                    "SELECT COUNT(*) FROM article_cards WHERE COALESCE(article_id, '') = ''"
                ).fetchone()[0]
            )
        finally:
            connection.close()
    except Exception:
        temp_db.unlink(missing_ok=True)
        raise

    if after_count < before_count:
        temp_db.unlink(missing_ok=True)
        raise RegistryWorkbenchError(
            f"non-destructive invariant failed: {after_count} < {before_count}"
        )

    temp_sha = _sha256_file(temp_db)
    temp_db.replace(active_db)

    manifest = dict(existing_manifest or {})
    manifest.update(
        {
            "schema_version": int(manifest.get("schema_version") or 1),
            "workbench_type": WORKBENCH_SCHEMA,
            "status": "PASS",
            "created_at": _now(),
            "counts": {
                "articles": after_count,
                "evidence_excerpts": excerpt_count,
                "result_bundles": bundle_count,
            },
            "outputs": {
                **dict(manifest.get("outputs") or {}),
                "database": {"path": str(active_db), "sha256": temp_sha},
            },
            "performance_contract": {
                **dict(manifest.get("performance_contract") or {}),
                "browser_loads_full_corpus": False,
                "server_side_filtering": True,
                "page_limit_max": 100,
                "detail_loaded_on_demand": True,
            },
            "guardrail": (
                "The cumulative Workbench is a non-destructive projection of Article Registry "
                "identity plus existing hash-verified scientific artifacts. Registry presence "
                "does not imply inclusion, quality, certainty, causality, recommendation, or PRISMA."
            ),
        }
    )
    extensions = dict(manifest.get("extensions") or {})
    extensions["article_registry"] = {
        "status": "PASS",
        "registry_database": str(registry_db),
        "registry_sha256": registry_sha,
        "registry_articles": len(registry_articles),
        "workbench_articles_before": before_count,
        "workbench_articles_after": after_count,
        "linked_existing": linked_existing,
        "inserted_registry_only": inserted_registry_only,
        "linked_article_ids": linked_count,
        "legacy_rows_preserved": legacy_preserved,
        "legacy_identity_ambiguities": legacy_identity_ambiguities,
        "non_destructive": after_count >= before_count,
        "identity_link_policy": "existing article_id, then exact DOI/PMID only; no fuzzy merge",
    }
    manifest["extensions"] = extensions
    _atomic_json(workbench_root / "WORKBENCH_MANIFEST.json", manifest)

    return {
        "status": "COMPLETE_WITH_LEGACY_AMBIGUITIES" if legacy_identity_ambiguities else "COMPLETE",
        "registry_articles": len(registry_articles),
        "articles_before": before_count,
        "articles_after": after_count,
        "linked_existing": linked_existing,
        "inserted_registry_only": inserted_registry_only,
        "linked_article_ids": linked_count,
        "legacy_rows_preserved": legacy_preserved,
        "legacy_identity_ambiguities": legacy_identity_ambiguities,
        "evidence_excerpts": excerpt_count,
        "result_bundles": bundle_count,
        "database": str(active_db),
        "database_sha256": temp_sha,
        "registry_sha256": registry_sha,
        "integrity_check": "ok",
        "non_destructive": after_count >= before_count,
    }
