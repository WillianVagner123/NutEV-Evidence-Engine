from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from nutev.registry.history_migration import run_history_migration_dry_run


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def search(search_id: str, rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "search_id": search_id,
        "query": "protein during energy restriction",
        "search_mode": "interactive_bounded",
        "status": "COMPLETE",
        "created_at": "2026-01-01T00:00:00+00:00",
        "providers": [],
        "results": rows,
        "records_before_dedup": len(rows),
        "unique_records": len(rows),
        "returned_records": len(rows),
    }


def write_native_core(root: Path) -> tuple[Path, Path]:
    core_root = root / "scientific" / "core"
    records = core_root / "nutev_core_records.jsonl"
    manifest = core_root / "CORE_MANIFEST.json"
    core_root.mkdir(parents=True, exist_ok=True)
    record = {
        "id": "nutev-core:article-a",
        "document_id": "legacy-doc-a",
        "schema_version": 1,
        "identity": {
            "title": "Article A",
            "doi": "10.1000/article-a",
            "pmid": "1001",
            "year": 2020,
            "source_provider": "pubmed",
        },
        "bibliographic": {"journal": "Journal A"},
        "provenance": {
            "evidence_record_id": "evidence:a",
            "origin_sha256": "1" * 64,
            "source_files_sha256": {"legacy": "2" * 64},
        },
        "acquisition": {
            "artifact_sha256": "3" * 64,
            "text_sha256": "4" * 64,
            "full_text_status": "retrieved",
        },
        "structure": {},
        "classification": {"document_class": "primary_observational"},
        "main_findings": [],
        "scores": {},
        "workflow": {"core_status": "materialized"},
        "content_refs": {},
        "guardrails": {"test_fixture_only": True},
        "generated_at": "2026-01-03T00:00:00+00:00",
    }
    records.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    write_json(
        manifest,
        {
            "schema_version": 1,
            "core_type": "NUTEV_CORE_EVIDENCE_BANK",
            "status": "PASS",
            "outputs": {
                "core_records": {
                    "path": str(records),
                    "sha256": file_sha(records),
                }
            },
        },
    )
    return records, manifest


def write_native_workbench(root: Path) -> tuple[Path, Path]:
    workbench_root = root / "scientific" / "workbench"
    database = workbench_root / "evidence_workbench.sqlite"
    manifest = workbench_root / "WORKBENCH_MANIFEST.json"
    workbench_root.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    try:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE article_cards (
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
            CREATE TABLE evidence_excerpts (
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
            CREATE TABLE result_bundles (
                result_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                result_kind TEXT NOT NULL,
                priority_score REAL NOT NULL,
                result_json TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES article_cards(document_id)
            );
            CREATE TABLE workbench_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """
        )
        card = {
            "document_id": "legacy-doc-c",
            "identity": {
                "title": "Article C",
                "doi": "10.1000/article-c",
                "pmid": "1003",
                "year": 2022,
            },
            "study_snapshot": {"legacy_preserved": True},
        }
        connection.execute(
            "INSERT INTO article_cards(document_id, record_id, title, year, doi, pmid, "
            "source_provider, document_class, full_text_status, cache_key, reference_stub, "
            "llm_context_chars, search_text, card_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "legacy-doc-c",
                "legacy-record-c",
                "Article C",
                2022,
                "10.1000/article-c",
                "1003",
                "legacy_workbench",
                "primary_observational",
                "retrieved",
                "legacy:c",
                "Article C. Legacy Journal. 2022",
                100,
                "article c legacy",
                json.dumps(card, sort_keys=True),
            ),
        )
        connection.execute(
            "INSERT INTO evidence_excerpts(excerpt_id, document_id, kind, section, locator, "
            "priority_score, verbatim_excerpt, excerpt_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "excerpt-c",
                "legacy-doc-c",
                "finding",
                "Results",
                "p. 3",
                5.0,
                "Legacy excerpt preserved.",
                json.dumps({"legacy": True}),
            ),
        )
        connection.execute(
            "INSERT INTO result_bundles(result_id, document_id, result_kind, priority_score, "
            "result_json) VALUES (?, ?, ?, ?, ?)",
            (
                "result-c",
                "legacy-doc-c",
                "finding_bundle",
                5.0,
                json.dumps({"legacy": True}),
            ),
        )
        connection.commit()
    finally:
        connection.close()
    write_json(
        manifest,
        {
            "schema_version": 1,
            "workbench_type": "NUTEV_ARTICLE_WORKBENCH_V1",
            "status": "PASS",
            "outputs": {
                "database": {
                    "path": str(database),
                    "sha256": file_sha(database),
                }
            },
        },
    )
    return database, manifest


def test_dry_run_uses_native_registry_core_workbench_and_never_mutates_legacy(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project_output_reference"
    first_search = root / "15_web_searches" / "s1" / "result.json"
    second_search = root / "bank" / "searches" / "s2" / "result.json"
    conflict_file = root / "scientific" / "core" / "legacy_core.json"
    full_text = root / "16_search_full_text_cache" / "article-a" / "manifest.json"
    unmatched_full_text = root / "16_search_full_text_cache" / "unmatched" / "manifest.json"
    unrelated = root / "unrelated.json"

    write_json(
        first_search,
        search(
            "legacy-search-1",
            [
                {
                    "title": "Article A",
                    "year": 2020,
                    "doi": "10.1000/article-a",
                    "pmid": "1001",
                    "source_provider": "pubmed",
                    "reference_rank": 1,
                },
                {
                    "title": "Article B",
                    "year": 2021,
                    "doi": "10.1000/article-b",
                    "pmid": "1002",
                    "source_provider": "pubmed",
                    "reference_rank": 2,
                },
            ],
        ),
    )
    write_json(
        second_search,
        search(
            "legacy-search-2",
            [
                {
                    "title": "Article A enriched",
                    "year": 2020,
                    "pmid": "1001",
                    "source_provider": "europepmc",
                    "reference_rank": 1,
                },
                {
                    "title": "Article C",
                    "year": 2022,
                    "doi": "10.1000/article-c",
                    "pmid": "1003",
                    "source_provider": "openalex",
                    "reference_rank": 2,
                },
            ],
        ),
    )
    write_json(
        conflict_file,
        {
            "title": "Article B conflicting manifestation",
            "year": 2021,
            "pmid": "1002",
            "doi": "10.1000/article-b-conflict",
            "source_provider": "legacy_core",
        },
    )
    write_json(
        full_text,
        {
            "title": "Article A",
            "year": 2020,
            "doi": "10.1000/article-a",
            "selected_url": "https://example.org/article-a.pdf",
            "content_sha256": "a" * 64,
            "private_text_sha256": "b" * 64,
            "media_type": "application/pdf",
            "extraction_method": "fixture",
            "ocr_used": False,
            "text_chars": 1234,
            "retrieved_at": "2026-01-02T00:00:00+00:00",
        },
    )
    write_json(
        unmatched_full_text,
        {
            "selected_url": "https://example.org/no-identity.pdf",
            "content_sha256": "c" * 64,
            "private_text_sha256": "d" * 64,
            "media_type": "application/pdf",
            "extraction_method": "fixture",
            "ocr_used": True,
            "ocr_engine": "fixture",
            "text_chars": 4321,
        },
    )
    write_json(
        unrelated,
        {
            "title": "Must not be imported from unrestricted output root",
            "year": 2024,
            "doi": "10.1000/unrelated",
        },
    )
    core_records, core_manifest = write_native_core(root)
    workbench_database, workbench_manifest = write_native_workbench(root)

    watched = [
        first_search,
        second_search,
        conflict_file,
        full_text,
        unmatched_full_text,
        unrelated,
        core_records,
        core_manifest,
        workbench_database,
        workbench_manifest,
    ]
    before = {path: file_sha(path) for path in watched}
    report_path = tmp_path / "REGISTRY_MIGRATION_REPORT.json"

    report = run_history_migration_dry_run(source_roots=[root], report_path=report_path)

    assert report["report_type"] == "NUTEV_REGISTRY_HISTORICAL_MIGRATION_DRY_RUN"
    assert report["status"] == "REVIEW_REQUIRED"
    assert report["records_seen"] >= 8
    assert report["unique_articles_created"] == 4
    assert report["search_runs_created"] == 2
    assert report["search_hits_created"] == 4
    assert report["aliases_created"] >= 6
    assert report["manifestations_created"] >= 6
    assert report["full_text_artifacts_linked"] == 1
    assert report["identity_conflicts"] == 1
    assert report["unmatched_full_text_cache"] == 1
    assert report["quarantined_records"] >= 1
    assert report["registry_integrity_check"] == "ok"

    assert report["core_records_seen"] == 1
    assert report["core_versions_created"] == 1
    assert report["core_versions_total"] == 1
    assert report["core_unresolved"] == 0
    assert report["core_identity_conflicts"] == 0
    assert report["core_projections"][0]["status"] == "COMPLETE"

    workbench = report["workbench_projection"]
    assert workbench["status"] == "STAGED"
    assert workbench["projection_status"] == "COMPLETE"
    assert workbench["articles_before"] == 1
    assert workbench["articles_after"] == 4
    assert workbench["linked_existing"] == 1
    assert workbench["evidence_excerpts"] == 1
    assert workbench["result_bundles"] == 1
    assert workbench["integrity_check"] == "ok"
    assert workbench["non_destructive"] is True

    assert not any(item["path"] == "unrelated.json" for item in report["source_inventory"]["files"])
    assert report["guardrails"] == {
        "dry_run": True,
        "temporary_registry_only": True,
        "temporary_core_projection_only": True,
        "temporary_workbench_projection_only": True,
        "target_registry_mutated": False,
        "legacy_files_modified": False,
        "legacy_files_deleted": False,
        "fuzzy_identity_merge": False,
        "scientific_inclusion_changed": False,
        "prisma_state_changed": False,
    }
    assert report_path.is_file()
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "REVIEW_REQUIRED"
    assert not (root / "registry").exists()
    assert {path: file_sha(path) for path in watched} == before


def test_missing_project_output_is_reported_not_interpreted_as_empty_evidence(tmp_path: Path) -> None:
    missing = tmp_path / "project_output_missing"
    report_path = tmp_path / "REGISTRY_MIGRATION_REPORT.json"

    report = run_history_migration_dry_run(source_roots=[missing], report_path=report_path)

    assert report["status"] == "SOURCE_NOT_MATERIALIZED"
    assert report["records_seen"] == 0
    assert report["unique_articles_created"] == 0
    assert report["next_gate"] == "mount_real_project_output_and_review_report"
    assert report["guardrails"]["target_registry_mutated"] is False
    assert report["guardrails"]["legacy_files_deleted"] is False


def test_legacy_search_without_id_gets_deterministic_migration_id(tmp_path: Path) -> None:
    root = tmp_path / "project_output"
    path = root / "15_web_searches" / "legacy" / "result.json"
    write_json(
        path,
        {
            "query": "dietary pattern",
            "created_at": "2020-01-01T00:00:00+00:00",
            "results": [
                {
                    "title": "Legacy article",
                    "year": 2019,
                    "doi": "10.1000/legacy",
                    "source_provider": "legacy",
                }
            ],
        },
    )

    first = run_history_migration_dry_run(
        source_roots=[root], report_path=tmp_path / "first.json"
    )
    second = run_history_migration_dry_run(
        source_roots=[root], report_path=tmp_path / "second.json"
    )

    assert first["status"] == "DRY_RUN_PASS"
    assert second["status"] == "DRY_RUN_PASS"
    assert first["search_runs_created"] == second["search_runs_created"] == 1
    assert first["search_hits_created"] == second["search_hits_created"] == 1
    assert first["unique_articles_created"] == second["unique_articles_created"] == 1
    assert first["workbench_projection"]["articles_after"] == 1
    assert second["workbench_projection"]["articles_after"] == 1
