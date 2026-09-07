from __future__ import annotations

import json
from pathlib import Path

from nutev.registry.history_migration import run_history_migration_dry_run


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_two_distinct_legacy_workbenches_require_human_reconciliation(tmp_path: Path) -> None:
    roots = [tmp_path / "project_output", tmp_path / "project_output_reference"]
    for index, root in enumerate(roots, start=1):
        workbench = root / "scientific" / "workbench"
        workbench.mkdir(parents=True, exist_ok=True)
        (workbench / "evidence_workbench.sqlite").write_bytes(f"distinct-{index}".encode())
        write_json(workbench / "WORKBENCH_MANIFEST.json", {"status": "PASS"})

    report = run_history_migration_dry_run(
        source_roots=roots,
        report_path=tmp_path / "REGISTRY_MIGRATION_REPORT.json",
    )

    assert report["status"] == "REVIEW_REQUIRED"
    assert report["workbench_projection"]["status"] == "MULTIPLE_DISTINCT_SOURCES"
    assert len(report["workbench_projection"]["sources"]) == 2
    assert any(
        item.get("reason") == "multiple_distinct_workbench_sources"
        for item in report["quarantine"]
    )
    assert report["guardrails"]["target_registry_mutated"] is False
    assert report["guardrails"]["legacy_files_deleted"] is False


def test_core_manifest_hash_mismatch_never_creates_core_version(tmp_path: Path) -> None:
    root = tmp_path / "project_output"
    core = root / "scientific" / "core"
    records = core / "nutev_core_records.jsonl"
    manifest = core / "CORE_MANIFEST.json"
    core.mkdir(parents=True, exist_ok=True)
    record = {
        "id": "nutev-core:hash-mismatch",
        "schema_version": 1,
        "identity": {
            "title": "Hash mismatch article",
            "doi": "10.1000/hash-mismatch",
            "year": 2024,
            "source_provider": "legacy_core",
        },
        "bibliographic": {},
        "provenance": {},
        "acquisition": {},
        "structure": {},
        "classification": {},
        "main_findings": [],
        "scores": {},
        "workflow": {},
        "content_refs": {},
        "guardrails": {},
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
                    "sha256": "0" * 64,
                }
            },
        },
    )

    report = run_history_migration_dry_run(
        source_roots=[root],
        report_path=tmp_path / "REGISTRY_MIGRATION_REPORT.json",
    )

    assert report["status"] == "REVIEW_REQUIRED"
    assert report["core_records_seen"] == 1
    assert report["core_versions_created"] == 0
    assert report["core_versions_total"] == 0
    assert any(
        item.get("reason") == "core_projection_failed" and "SHA-256 mismatch" in item.get("error", "")
        for item in report["quarantine"]
    )
    assert report["guardrails"]["temporary_core_projection_only"] is True
    assert report["guardrails"]["target_registry_mutated"] is False
