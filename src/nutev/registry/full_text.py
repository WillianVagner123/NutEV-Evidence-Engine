from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import sqlite3
from typing import Any

from .sqlite_store import SQLiteArticleRegistry


def _now(value: str | None = None) -> str:
    return str(value or datetime.now(timezone.utc).isoformat())


def _text(value: Any) -> str:
    return str(value or "").strip()


def _relative_storage_path(path: Path, output_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(output_root.resolve()))
    except ValueError:
        return str(path.resolve())


def record_full_text_artifact(
    *,
    output_root: Path,
    article_id: str,
    manifest: dict[str, Any],
    cache_dir: Path,
) -> dict[str, Any]:
    """Record one extracted document version without storing its text body in SQLite."""

    article_id = _text(article_id)
    if not article_id:
        return {"status": "not_linked", "reason": "missing_article_id"}
    content_sha = _text(manifest.get("content_sha256")).lower()
    text_sha = _text(manifest.get("private_text_sha256") or manifest.get("text_sha256")).lower()
    if len(content_sha) != 64 or len(text_sha) != 64:
        return {"status": "not_linked", "reason": "missing_content_or_text_sha256"}

    registry_root = Path(output_root) / "registry"
    registry = SQLiteArticleRegistry(
        registry_root / "article_registry.sqlite",
        registry_root / "ARTICLE_REGISTRY_MANIFEST.json",
    )
    with registry._connect() as connection:
        article = connection.execute(
            "SELECT 1 FROM articles WHERE article_id = ?",
            (article_id,),
        ).fetchone()
        if article is None:
            return {"status": "not_linked", "reason": "article_id_not_in_registry"}

        retrieved_at = _now(_text(manifest.get("retrieved_at")) or None)
        artifact_seed = f"{article_id}|{content_sha}"
        artifact_id = "NUTEV-FT-" + sha256(artifact_seed.encode("utf-8")).hexdigest()[:24]
        existing = connection.execute(
            "SELECT artifact_id FROM full_text_artifacts WHERE article_id = ? AND content_sha256 = ?",
            (article_id, content_sha),
        ).fetchone()
        created = existing is None
        if existing is not None:
            artifact_id = str(existing["artifact_id"])
        connection.execute(
            """
            INSERT INTO full_text_artifacts(
                artifact_id, article_id, source_url, resolver_source, resolver_route, media_type,
                content_sha256, text_sha256, extraction_method, ocr_used, ocr_engine, text_chars,
                retrieved_at, storage_path, cache_key, status, created_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'extracted', ?, ?)
            ON CONFLICT(article_id, content_sha256) DO UPDATE SET
                source_url = excluded.source_url,
                resolver_source = excluded.resolver_source,
                resolver_route = excluded.resolver_route,
                media_type = excluded.media_type,
                text_sha256 = excluded.text_sha256,
                extraction_method = excluded.extraction_method,
                ocr_used = excluded.ocr_used,
                ocr_engine = excluded.ocr_engine,
                text_chars = excluded.text_chars,
                last_seen_at = excluded.last_seen_at,
                status = 'extracted'
            """,
            (
                artifact_id,
                article_id,
                _text(manifest.get("selected_url")),
                _text(manifest.get("resolver_source")),
                _text(manifest.get("resolver_route")),
                _text(manifest.get("media_type")),
                content_sha,
                text_sha,
                _text(manifest.get("extraction_method")),
                1 if manifest.get("ocr_used") else 0,
                _text(manifest.get("ocr_engine")),
                int(manifest.get("text_chars") or 0),
                retrieved_at,
                _relative_storage_path(cache_dir, Path(output_root)),
                _text(manifest.get("cache_key")),
                retrieved_at,
                retrieved_at,
            ),
        )
        connection.commit()
    registry._write_manifest()
    return {
        "status": "linked",
        "article_id": article_id,
        "artifact_id": artifact_id,
        "created": created,
        "content_sha256": content_sha,
        "text_sha256": text_sha,
    }


def list_full_text_artifacts(*, output_root: Path, article_id: str) -> list[dict[str, Any]]:
    registry_root = Path(output_root) / "registry"
    database = registry_root / "article_registry.sqlite"
    if not database.is_file():
        return []
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT * FROM full_text_artifacts WHERE article_id = ? ORDER BY retrieved_at, artifact_id",
            (article_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
