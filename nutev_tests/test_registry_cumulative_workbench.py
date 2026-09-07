from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from nutev.registry.ingest import register_search_result
from nutev.registry.workbench import (
    RegistryWorkbenchError,
    _create_base_schema,
    _sha256_file,
    refresh_cumulative_workbench,
)


def _row(index: int, *, provider: str = "pubmed") -> dict:
    return {
        "title": f"Article {index}",
        "doi": f"10.1000/article-{index}",
        "pmid": str(10_000_000 + index),
        "source_provider": provider,
        "source": provider,
        "provider_query": "nutrition",
        "interactive_retrieved_at": "2026-09-07T12:00:00+00:00",
        "reference_rank": index + 1,
        "reference_score": 90.0,
        "query_relevance_score": 80.0,
        "nutev_priority_score": 70.0,
    }


def _result(search_id: str, indexes: range, *, provider: str = "pubmed") -> dict:
    rows = [_row(index, provider=provider) for index in indexes]
    return {
        "schema_version": 3,
        "search_id": search_id,
        "query": "nutrition",
        "created_at": "2026-09-07T12:00:00+00:00",
        "search_mode": "global_exhaustive",
        "status": "COMPLETE",
        "providers": [{"provider": provider, "status": "completed", "returned": len(rows)}],
        "failed_providers": [],
        "unavailable_providers": [],
        "non_exhaustive_providers": [],
        "records_before_dedup": len(rows),
        "unique_records": len(rows),
        "returned_records": len(rows),
        "results": rows,
    }


def _workbench_paths(root: Path) -> tuple[Path, Path]:
    workbench = root / "scientific" / "workbench"
    return workbench / "evidence_workbench.sqlite", workbench / "WORKBENCH_MANIFEST.json"


def _write_existing_workbench(root: Path, rows: list[dict], *, with_evidence: bool = False) -> list[str]:
    database, manifest = _workbench_paths(root)
    database.parent.mkdir(parents=True, exist_ok=True)
    document_ids: list[str] = []
    connection = sqlite3.connect(database)
    try:
        _create_base_schema(connection)
        for index, row in enumerate(rows):
            document_id = f"legacy-doc-{index:04d}"
            document_ids.append(document_id)
            card = {
                "document_id": document_id,
                "record_id": f"legacy-record-{index:04d}",
                "identity": {
                    "title": row["title"],
                    "doi": row.get("doi"),
                    "pmid": row.get("pmid"),
                    "year": 2025,
                    "source_provider": row.get("source_provider", "legacy"),
                },
                "reference": {"journal": "Legacy Journal", "reference_stub": row["title"]},
                "study_snapshot": {"population": ["adults"]},
                "document_class": "primary_observational",
                "full_text_status": "extracted",
                "cache_key": f"legacy:{index}",
                "llm_context_chars": 1234,
            }
            search_text = f"{row['title']} {row.get('doi', '')} adults".casefold()
            connection.execute(
                """
                INSERT INTO article_cards(
                    document_id, record_id, title, year, doi, pmid, source_provider,
                    document_class, full_text_status, cache_key, reference_stub,
                    llm_context_chars, search_text, card_json
                ) VALUES (?, ?, ?, 2025, ?, ?, ?, 'primary_observational', 'extracted', ?, ?, 1234, ?, ?)
                """,
                (
                    document_id,
                    f"legacy-record-{index:04d}",
                    row["title"],
                    row.get("doi"),
                    row.get("pmid"),
                    row.get("source_provider", "legacy"),
                    f"legacy:{index}",
                    row["title"],
                    search_text,
                    json.dumps(card, sort_keys=True),
                ),
            )
        if with_evidence and document_ids:
            document_id = document_ids[0]
            connection.execute(
                "INSERT INTO evidence_excerpts(excerpt_id, document_id, kind, section, locator, priority_score, verbatim_excerpt, excerpt_json) VALUES (?, ?, 'finding', 'results', 'p1', 9.0, 'Observed result', ?)",
                (
                    "legacy-excerpt-1",
                    document_id,
                    json.dumps(
                        {
                            "id": "legacy-excerpt-1",
                            "document_id": document_id,
                            "kind": "finding",
                            "section": "results",
                            "locator": "p1",
                            "priority_score": 9.0,
                            "verbatim_excerpt": "Observed result",
                        },
                        sort_keys=True,
                    ),
                ),
            )
            connection.execute(
                "INSERT INTO result_bundles(result_id, document_id, result_kind, priority_score, result_json) VALUES (?, ?, 'finding', 9.0, ?)",
                (
                    "legacy-result-1",
                    document_id,
                    json.dumps(
                        {
                            "id": "legacy-result-1",
                            "document_id": document_id,
                            "result_kind": "finding",
                            "priority_score": 9.0,
                        },
                        sort_keys=True,
                    ),
                ),
            )
        connection.commit()
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        connection.close()

    sha = _sha256_file(database)
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "workbench_type": "NUTEV_ARTICLE_WORKBENCH_V1",
                "status": "PASS",
                "created_at": "2026-09-07T11:00:00+00:00",
                "counts": {
                    "articles": len(rows),
                    "evidence_excerpts": 1 if with_evidence and rows else 0,
                    "result_bundles": 1 if with_evidence and rows else 0,
                },
                "outputs": {"database": {"path": str(database), "sha256": sha}},
                "extensions": {"legacy_test": {"status": "PASS"}},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return document_ids


def test_registry_only_workbench_grows_cumulatively_and_preserves_article_ids(tmp_path: Path) -> None:
    first = _result("web_a", range(0, 100))
    register_search_result(first, output_root=tmp_path)
    first_ids = [row["article_id"] for row in first["results"]]
    projected = refresh_cumulative_workbench(output_root=tmp_path)

    assert projected["articles_before"] == 0
    assert projected["articles_after"] == 100
    assert projected["inserted_registry_only"] == 100
    assert projected["integrity_check"] == "ok"

    second = _result("web_b", range(70, 120), provider="crossref")
    register_search_result(second, output_root=tmp_path)
    projected_again = refresh_cumulative_workbench(output_root=tmp_path)

    assert projected_again["articles_before"] == 100
    assert projected_again["articles_after"] == 120
    assert projected_again["non_destructive"] is True

    database, _manifest = _workbench_paths(tmp_path)
    connection = sqlite3.connect(database)
    try:
        current_ids = {
            row[0]
            for row in connection.execute("SELECT document_id FROM article_cards").fetchall()
        }
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        connection.close()
    assert set(first_ids) <= current_ids


def test_existing_rich_workbench_is_linked_and_never_replaced(tmp_path: Path) -> None:
    legacy_rows = [_row(index) for index in range(100)]
    legacy_ids = _write_existing_workbench(tmp_path, legacy_rows, with_evidence=True)

    registry_result = _result("web_registry", range(50, 120), provider="crossref")
    register_search_result(registry_result, output_root=tmp_path)
    projected = refresh_cumulative_workbench(output_root=tmp_path)

    assert projected["articles_before"] == 100
    assert projected["linked_existing"] == 50
    assert projected["inserted_registry_only"] == 20
    assert projected["articles_after"] == 120
    assert projected["evidence_excerpts"] == 1
    assert projected["result_bundles"] == 1
    assert projected["legacy_rows_preserved"] == 50

    database, manifest_path = _workbench_paths(tmp_path)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        existing = {
            row["document_id"]
            for row in connection.execute("SELECT document_id FROM article_cards").fetchall()
        }
        linked = connection.execute(
            "SELECT article_id, registry_scope, card_json FROM article_cards WHERE document_id = ?",
            (legacy_ids[50],),
        ).fetchone()
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT COUNT(*) FROM evidence_excerpts").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM result_bundles").fetchone()[0] == 1
    finally:
        connection.close()

    assert set(legacy_ids) <= existing
    assert linked is not None
    assert linked["article_id"].startswith("NUTEV-ART-")
    assert linked["registry_scope"] == "registry_linked"
    linked_card = json.loads(linked["card_json"])
    assert linked_card["study_snapshot"] == {"population": ["adults"]}
    assert linked_card["registry"]["scope"] == "global_article_registry"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "PASS"
    assert manifest["counts"]["articles"] == 120
    assert manifest["extensions"]["legacy_test"]["status"] == "PASS"
    extension = manifest["extensions"]["article_registry"]
    assert extension["non_destructive"] is True
    assert extension["identity_link_policy"].startswith("existing article_id, then exact DOI/PMID")
    assert _sha256_file(database) == manifest["outputs"]["database"]["sha256"]


def test_repeated_projection_is_idempotent(tmp_path: Path) -> None:
    result = _result("web_repeat", range(0, 25))
    register_search_result(result, output_root=tmp_path)
    first = refresh_cumulative_workbench(output_root=tmp_path)
    second = refresh_cumulative_workbench(output_root=tmp_path)

    assert first["articles_after"] == 25
    assert second["articles_before"] == 25
    assert second["articles_after"] == 25
    assert second["inserted_registry_only"] == 0
    assert second["integrity_check"] == "ok"


def test_ambiguous_legacy_identity_is_not_destructively_collapsed(tmp_path: Path) -> None:
    duplicate = _row(0)
    _write_existing_workbench(tmp_path, [duplicate, duplicate])
    result = _result("web_ambiguous", range(0, 1))
    register_search_result(result, output_root=tmp_path)

    projected = refresh_cumulative_workbench(output_root=tmp_path)

    assert projected["status"] == "COMPLETE_WITH_LEGACY_AMBIGUITIES"
    assert projected["legacy_identity_ambiguities"] == 1
    assert projected["articles_before"] == 2
    assert projected["articles_after"] == 3
    assert projected["legacy_rows_preserved"] == 2


def test_bad_existing_manifest_hash_blocks_switch_and_preserves_active_database(tmp_path: Path) -> None:
    _write_existing_workbench(tmp_path, [_row(0), _row(1)])
    database, manifest_path = _workbench_paths(tmp_path)
    before_bytes = database.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["outputs"]["database"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    register_search_result(_result("web_new", range(2, 4)), output_root=tmp_path)

    try:
        refresh_cumulative_workbench(output_root=tmp_path)
    except RegistryWorkbenchError as exc:
        assert "SHA-256 mismatch" in str(exc)
    else:
        raise AssertionError("projection should fail closed on invalid source Workbench")

    assert database.read_bytes() == before_bytes


def test_registry_projection_never_moves_rank_or_quality_into_article_identity(tmp_path: Path) -> None:
    result = _result("web_rank", range(0, 3))
    result["results"][0]["reference_rank"] = 77
    result["results"][0]["reference_score"] = 12.3
    register_search_result(result, output_root=tmp_path)
    refresh_cumulative_workbench(output_root=tmp_path)

    database, _manifest = _workbench_paths(tmp_path)
    connection = sqlite3.connect(database)
    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(article_cards)").fetchall()
        }
        registry_columns = {
            row[1]
            for row in sqlite3.connect(
                tmp_path / "registry" / "article_registry.sqlite"
            ).execute("PRAGMA table_info(articles)").fetchall()
        }
    finally:
        connection.close()

    assert "article_id" in columns
    assert "reference_rank" not in registry_columns
    assert "reference_score" not in registry_columns
