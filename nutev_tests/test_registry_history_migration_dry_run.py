from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

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


def test_dry_run_uses_real_registry_identity_and_never_mutates_legacy(tmp_path: Path) -> None:
    root = tmp_path / "project_output_reference"
    first_search = root / "15_web_searches" / "s1" / "result.json"
    second_search = root / "bank" / "searches" / "s2" / "result.json"
    conflict_file = root / "scientific" / "core" / "legacy_core.json"
    workbench_file = root / "scientific" / "workbench" / "legacy_workbench.json"
    full_text = root / "16_search_full_text_cache" / "article-a" / "manifest.json"
    unmatched_full_text = root / "16_search_full_text_cache" / "unmatched" / "manifest.json"

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
        workbench_file,
        {
            "documents": [
                {
                    "title": "Article C",
                    "year": 2022,
                    "doi": "10.1000/article-c",
                    "source_provider": "legacy_workbench",
                }
            ]
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

    watched = [first_search, second_search, conflict_file, workbench_file, full_text, unmatched_full_text]
    before = {path: file_sha(path) for path in watched}
    report_path = tmp_path / "REGISTRY_MIGRATION_REPORT.json"

    report = run_history_migration_dry_run(source_roots=[root], report_path=report_path)

    assert report["report_type"] == "NUTEV_REGISTRY_HISTORICAL_MIGRATION_DRY_RUN"
    assert report["status"] == "REVIEW_REQUIRED"
    assert report["records_seen"] >= 7
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
    assert report["guardrails"] == {
        "dry_run": True,
        "temporary_registry_only": True,
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
