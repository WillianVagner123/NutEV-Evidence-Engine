from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 3

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS registry_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS articles (
    article_id TEXT PRIMARY KEY,
    canonical_title TEXT NOT NULL DEFAULT '',
    publication_year INTEGER,
    journal TEXT NOT NULL DEFAULT '',
    abstract TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    registry_status TEXT NOT NULL DEFAULT 'active'
        CHECK (registry_status IN ('active', 'identity_conflict', 'quarantined'))
);
CREATE INDEX IF NOT EXISTS idx_articles_year ON articles(publication_year DESC);
CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(canonical_title);
CREATE INDEX IF NOT EXISTS idx_articles_last_seen ON articles(last_seen_at DESC);

CREATE TABLE IF NOT EXISTS article_aliases (
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    scheme TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    raw_value TEXT NOT NULL DEFAULT '',
    provider TEXT NOT NULL DEFAULT '',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    UNIQUE(scheme, normalized_value)
);
CREATE INDEX IF NOT EXISTS idx_alias_article ON article_aliases(article_id);
CREATE INDEX IF NOT EXISTS idx_alias_scheme ON article_aliases(scheme);

CREATE TABLE IF NOT EXISTS article_manifestations (
    manifestation_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    provider TEXT NOT NULL DEFAULT '',
    provider_record_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    abstract TEXT NOT NULL DEFAULT '',
    authors_json TEXT NOT NULL DEFAULT '[]',
    journal TEXT NOT NULL DEFAULT '',
    publication_year INTEGER,
    raw_identifiers_json TEXT NOT NULL DEFAULT '{}',
    retrieved_at TEXT NOT NULL,
    source_payload_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(article_id, provider, provider_record_id, source_payload_hash)
);
CREATE INDEX IF NOT EXISTS idx_manifest_article ON article_manifestations(article_id);
CREATE INDEX IF NOT EXISTS idx_manifest_provider ON article_manifestations(provider);

CREATE TABLE IF NOT EXISTS article_field_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    value_json TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT '',
    observed_at TEXT NOT NULL,
    precedence_rule TEXT NOT NULL,
    source_payload_hash TEXT NOT NULL,
    UNIQUE(article_id, field_name, value_json, provider, source_payload_hash)
);
CREATE INDEX IF NOT EXISTS idx_field_history_article ON article_field_history(article_id);
CREATE INDEX IF NOT EXISTS idx_field_history_field ON article_field_history(field_name);

CREATE TABLE IF NOT EXISTS search_runs (
    search_id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    search_mode TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    provider_plan_json TEXT NOT NULL DEFAULT '{}',
    provider_gaps_json TEXT NOT NULL DEFAULT '[]',
    search_manifest_hash TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS search_hits (
    hit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_id TEXT NOT NULL REFERENCES search_runs(search_id) ON DELETE CASCADE,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE RESTRICT,
    provider TEXT NOT NULL DEFAULT '',
    provider_query TEXT NOT NULL DEFAULT '',
    provider_position INTEGER,
    reference_rank INTEGER,
    reference_score REAL,
    query_relevance_score REAL,
    nutev_priority_score REAL,
    retrieved_at TEXT NOT NULL,
    source_manifestation_id TEXT REFERENCES article_manifestations(manifestation_id)
);
CREATE INDEX IF NOT EXISTS idx_hit_search ON search_hits(search_id);
CREATE INDEX IF NOT EXISTS idx_hit_article ON search_hits(article_id);
CREATE INDEX IF NOT EXISTS idx_hit_provider ON search_hits(provider);

CREATE TABLE IF NOT EXISTS identity_conflicts (
    conflict_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL UNIQUE,
    candidate_article_ids_json TEXT NOT NULL,
    identifiers_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'resolved_same_article', 'resolved_different_articles')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conflict_status ON identity_conflicts(status);

CREATE TABLE IF NOT EXISTS full_text_artifacts (
    artifact_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    source_url TEXT NOT NULL DEFAULT '',
    resolver_source TEXT NOT NULL DEFAULT '',
    resolver_route TEXT NOT NULL DEFAULT '',
    media_type TEXT NOT NULL DEFAULT '',
    content_sha256 TEXT NOT NULL,
    text_sha256 TEXT NOT NULL,
    extraction_method TEXT NOT NULL DEFAULT '',
    ocr_used INTEGER NOT NULL DEFAULT 0 CHECK (ocr_used IN (0, 1)),
    ocr_engine TEXT NOT NULL DEFAULT '',
    text_chars INTEGER NOT NULL DEFAULT 0,
    retrieved_at TEXT NOT NULL,
    storage_path TEXT NOT NULL DEFAULT '',
    cache_key TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'extracted'
        CHECK (status IN ('extracted', 'superseded', 'quarantined')),
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    UNIQUE(article_id, content_sha256)
);
CREATE INDEX IF NOT EXISTS idx_full_text_article ON full_text_artifacts(article_id);
CREATE INDEX IF NOT EXISTS idx_full_text_content_sha ON full_text_artifacts(content_sha256);
CREATE INDEX IF NOT EXISTS idx_full_text_ocr ON full_text_artifacts(ocr_used);
CREATE INDEX IF NOT EXISTS idx_full_text_status ON full_text_artifacts(status);

CREATE TABLE IF NOT EXISTS core_versions (
    core_version_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    core_record_id TEXT NOT NULL DEFAULT '',
    source_document_id TEXT NOT NULL DEFAULT '',
    record_sha256 TEXT NOT NULL,
    input_artifact_hashes_json TEXT NOT NULL DEFAULT '{}',
    pipeline_version TEXT NOT NULL DEFAULT '',
    generated_at TEXT NOT NULL,
    record_json TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    created_at TEXT NOT NULL,
    UNIQUE(article_id, version_number),
    UNIQUE(article_id, record_sha256)
);
CREATE INDEX IF NOT EXISTS idx_core_version_article ON core_versions(article_id);
CREATE INDEX IF NOT EXISTS idx_core_version_current ON core_versions(article_id, is_current);
CREATE UNIQUE INDEX IF NOT EXISTS idx_core_one_current_per_article
    ON core_versions(article_id) WHERE is_current = 1;
"""


def apply_migrations(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.execute(
        "INSERT INTO registry_meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(SCHEMA_VERSION),),
    )
    connection.execute(
        "INSERT INTO registry_meta(key, value) VALUES('semantic_contract', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (
            "article registry presence is discovery/indexing only; not inclusion, quality, "
            "certainty, recommendation, or PRISMA",
        ),
    )
    connection.commit()
