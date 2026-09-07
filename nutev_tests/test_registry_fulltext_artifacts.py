from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = REPO_ROOT / "apps" / "nutev-web"
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

from nutev.registry import SQLiteArticleRegistry
from nutev.registry.full_text import list_full_text_artifacts, record_full_text_artifact

import search_fulltext


def _article(tmp_path: Path, *, doi: str = "10.1000/fulltext") -> str:
    registry = SQLiteArticleRegistry(tmp_path / "registry" / "article_registry.sqlite")
    result = registry.register_article(
        {
            "source_provider": "pubmed",
            "doi": doi,
            "pmid": "12345678",
            "title": "Full text article",
        }
    )
    assert result.article_id is not None
    return result.article_id


def _manifest(*, content_sha: str, text_sha: str, ocr: bool = False) -> dict:
    return {
        "status": "extracted",
        "selected_url": "https://example.org/article.pdf",
        "resolver_source": "test",
        "resolver_route": "test_pdf",
        "media_type": "application/pdf",
        "content_sha256": content_sha,
        "private_text_sha256": text_sha,
        "extraction_method": "ocr_tesseract" if ocr else "pdf_text",
        "ocr_used": ocr,
        "ocr_engine": "tesseract" if ocr else "",
        "text_chars": 4321,
        "retrieved_at": "2026-09-07T12:00:00+00:00",
        "cache_key": "cache-key",
    }


def test_same_document_version_is_one_artifact_for_same_article(tmp_path: Path) -> None:
    article_id = _article(tmp_path)
    cache = tmp_path / "16_search_full_text_cache" / "one"
    cache.mkdir(parents=True)
    content_sha = "a" * 64
    text_sha = "b" * 64

    first = record_full_text_artifact(
        output_root=tmp_path,
        article_id=article_id,
        manifest=_manifest(content_sha=content_sha, text_sha=text_sha, ocr=True),
        cache_dir=cache,
    )
    second = record_full_text_artifact(
        output_root=tmp_path,
        article_id=article_id,
        manifest=_manifest(content_sha=content_sha, text_sha=text_sha, ocr=True),
        cache_dir=cache,
    )

    assert first["status"] == second["status"] == "linked"
    assert first["created"] is True
    assert second["created"] is False
    assert first["artifact_id"] == second["artifact_id"]
    artifacts = list_full_text_artifacts(output_root=tmp_path, article_id=article_id)
    assert len(artifacts) == 1
    assert artifacts[0]["ocr_used"] == 1
    assert artifacts[0]["ocr_engine"] == "tesseract"


def test_new_content_hash_creates_new_version_without_overwriting_old(tmp_path: Path) -> None:
    article_id = _article(tmp_path)
    cache = tmp_path / "16_search_full_text_cache" / "versions"
    cache.mkdir(parents=True)

    record_full_text_artifact(
        output_root=tmp_path,
        article_id=article_id,
        manifest=_manifest(content_sha="1" * 64, text_sha="2" * 64),
        cache_dir=cache,
    )
    record_full_text_artifact(
        output_root=tmp_path,
        article_id=article_id,
        manifest=_manifest(content_sha="3" * 64, text_sha="4" * 64, ocr=True),
        cache_dir=cache,
    )

    artifacts = list_full_text_artifacts(output_root=tmp_path, article_id=article_id)
    assert len(artifacts) == 2
    assert {row["content_sha256"] for row in artifacts} == {"1" * 64, "3" * 64}
    assert {row["text_sha256"] for row in artifacts} == {"2" * 64, "4" * 64}


def test_cache_identity_prefers_article_id_over_provider_aliases(tmp_path: Path) -> None:
    article_id = _article(tmp_path)
    left = {
        "article_id": article_id,
        "doi": "10.1000/left-alias",
        "pmid": "11111111",
    }
    right = {
        "article_id": article_id,
        "doi": "10.1000/right-alias",
        "pmcid": "PMC9999999",
    }

    assert search_fulltext._cache_key(left) == search_fulltext._cache_key(right)
    assert search_fulltext._identity_seed(left) == f"article_id:{article_id}"


def test_real_enrichment_links_ocr_artifact_and_second_provider_reuses_cache(monkeypatch, tmp_path: Path) -> None:
    article_id = _article(tmp_path)
    candidate = {
        "url": "https://example.org/article.pdf",
        "scope": "full_text",
        "media_type": "application/pdf",
        "resolver_route": "test_pdf",
        "resolver_source": "test",
    }
    monkeypatch.setattr(
        search_fulltext,
        "_full_text_candidates",
        lambda _row, *, allow_network: [candidate],
    )
    monkeypatch.setattr(
        search_fulltext,
        "select_reachable_candidate",
        lambda candidates, **_kwargs: ({**candidates[0], "probe_selected": True}, [{"reachable": True}]),
    )

    downloaded = tmp_path / "source.pdf"
    downloaded.write_bytes(b"%PDF one immutable document version")
    calls = {"downloads": 0, "ocr": 0}

    def fake_download(_url: str, _target: Path):
        calls["downloads"] += 1
        return downloaded, "application/pdf", "https://example.org/article.pdf"

    def fake_extract(_path: Path, _media: str):
        calls["ocr"] += 1
        return (
            "ocr extracted full text " * 100,
            SimpleNamespace(value="ocr_tesseract"),
            True,
            "tesseract",
            [],
        )

    monkeypatch.setattr(search_fulltext, "_download", fake_download)
    monkeypatch.setattr(search_fulltext, "_extract_local_file", fake_extract)
    monkeypatch.setattr(
        search_fulltext,
        "_section_blocks",
        lambda _text, _document_id: (SimpleNamespace(heading="Methods"), SimpleNamespace(heading="Results")),
    )
    monkeypatch.setattr(
        search_fulltext,
        "_content_signals",
        lambda _text, _blocks: {"study_design_signals": ["randomized controlled trial"]},
    )

    first_row = {
        "article_id": article_id,
        "doi": "10.1000/fulltext",
        "source_provider": "pubmed",
        "reference_rank": 1,
        "reference_score": 90.0,
    }
    first = search_fulltext._enrich_one(first_row, output_root=tmp_path, allow_network=True)
    assert first["status"] == "extracted"
    assert first["ocr_used"] is True
    assert first["registry_linked"] is True
    assert first["artifact_id"].startswith("NUTEV-FT-")
    assert first["article_id"] == article_id
    assert first["cache_hit"] is False
    assert "private_text_file" not in first
    assert "private_text_sha256" not in first
    assert "text" not in first

    second_row = {
        "article_id": article_id,
        "openalex_id": "W123",
        "source_provider": "openalex",
        "reference_rank": 9,
        "reference_score": 40.0,
    }
    monkeypatch.setattr(
        search_fulltext,
        "_download",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("global cache must skip download")),
    )
    second = search_fulltext._enrich_one(second_row, output_root=tmp_path, allow_network=True)

    assert second["status"] == "extracted"
    assert second["cache_hit"] is True
    assert second["artifact_id"] == first["artifact_id"]
    assert calls == {"downloads": 1, "ocr": 1}
    assert len(list_full_text_artifacts(output_root=tmp_path, article_id=article_id)) == 1


def test_registry_stores_provenance_not_full_text_body(tmp_path: Path) -> None:
    article_id = _article(tmp_path)
    cache = tmp_path / "16_search_full_text_cache" / "private"
    cache.mkdir(parents=True)
    (cache / "private-text.txt").write_text("SECRET FULL TEXT BODY", encoding="utf-8")
    record_full_text_artifact(
        output_root=tmp_path,
        article_id=article_id,
        manifest=_manifest(content_sha="c" * 64, text_sha="d" * 64),
        cache_dir=cache,
    )

    database = tmp_path / "registry" / "article_registry.sqlite"
    assert b"SECRET FULL TEXT BODY" not in database.read_bytes()
    connection = sqlite3.connect(database)
    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(full_text_artifacts)").fetchall()
        }
        count = connection.execute(
            "SELECT COUNT(*) FROM full_text_artifacts WHERE article_id = ?",
            (article_id,),
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1
    assert "text_body" not in columns
    assert "content_sha256" in columns
    assert "text_sha256" in columns


def test_registry_schema_migrates_existing_v1_database_in_place(tmp_path: Path) -> None:
    registry = SQLiteArticleRegistry(tmp_path / "registry" / "article_registry.sqlite")
    created = registry.register_article(
        {"source_provider": "pubmed", "pmid": "87654321", "title": "Migration"}
    )
    article_id = created.article_id
    assert article_id is not None

    reopened = SQLiteArticleRegistry(registry.database_path)
    assert reopened.get_article(article_id) is not None
    connection = sqlite3.connect(registry.database_path)
    try:
        schema_version = connection.execute(
            "SELECT value FROM registry_meta WHERE key = 'schema_version'"
        ).fetchone()[0]
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='full_text_artifacts'"
        ).fetchone()
    finally:
        connection.close()
    assert schema_version == "2"
    assert table == ("full_text_artifacts",)
