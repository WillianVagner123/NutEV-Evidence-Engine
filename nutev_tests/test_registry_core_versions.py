from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from nutev.registry import SQLiteArticleRegistry
from nutev.registry.core import list_core_versions, project_core_records


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _registry_article(tmp_path: Path, *, doi: str = "10.1000/core", pmid: str = "12345678") -> str:
    registry = SQLiteArticleRegistry(tmp_path / "registry" / "article_registry.sqlite")
    created = registry.register_article(
        {
            "source_provider": "pubmed",
            "doi": doi,
            "pmid": pmid,
            "title": "Cumulative CORE article",
            "year": 2026,
            "journal": "Journal",
        }
    )
    assert created.article_id is not None
    return created.article_id


def _core_record(*, generated_at: str = "2026-09-07T12:00:00+00:00", text_sha: str = "a" * 64) -> dict:
    return {
        "id": "nutev-core:legacy-doc-1",
        "document_id": "legacy-doc-1",
        "evidence_record_id": "evidence:1",
        "schema_version": 1,
        "identity": {
            "title": "Cumulative CORE article",
            "doi": "10.1000/core",
            "pmid": "12345678",
            "url": "https://doi.org/10.1000/core",
            "year": 2026,
            "source_provider": "pubmed",
        },
        "bibliographic": {
            "abstract": "Observed abstract",
            "journal": "Journal",
            "authors": ["A Author"],
            "article_type": "journal article",
            "keywords": ["nutrition"],
        },
        "reference_layer": {
            "reference_rank": 1,
            "reference_score": 90.0,
            "guardrail": "reading priority only",
        },
        "provenance": {
            "evidence_record_id": "evidence:1",
            "source_provider": "pubmed",
            "source_run_id": "web_a",
            "origin_sha256": "b" * 64,
            "source_files_sha256": {
                "documents": "c" * 64,
                "enrichment": "d" * 64,
            },
        },
        "acquisition": {
            "artifact_id": "artifact:1",
            "full_text_status": "retrieved",
            "artifact_sha256": "e" * 64,
            "extraction_method": "ocr_tesseract",
            "ocr_used": True,
            "ocr_engine": "tesseract",
            "text_sha256": text_sha,
            "text_chars": 5000,
        },
        "structure": {"section_coverage": {"has_methods": True, "has_results": True}},
        "classification": {
            "document_class": "primary_randomized",
            "study_design_candidates": ["randomized controlled trial"],
        },
        "main_findings": [
            {
                "id": "finding:1",
                "document_id": "legacy-doc-1",
                "section": "Results",
                "locator": "p. 4",
                "source_excerpt": "Observed result.",
                "sentence_sha256": "f" * 64,
                "importance_score": 8.0,
                "signals": ["effect"],
                "status": "machine_candidate",
            }
        ],
        "scores": {
            "core_readiness": {
                "profile_id": "NUTEV_CORE_READINESS",
                "profile_version": "1",
                "status": "scored",
                "normalized_score": 80.0,
            },
            "mev": {"status": "not_scored", "reason": "no versioned MEV profile supplied"},
        },
        "workflow": {
            "core_status": "materialized",
            "prisma": "optional_downstream",
        },
        "content_refs": {"enrichment_id": "enrich:1"},
        "guardrails": {
            "main_findings_are_machine_candidates": True,
            "prisma_is_optional": True,
        },
        "generated_at": generated_at,
    }


def _write_core(tmp_path: Path, records: list[dict]) -> tuple[Path, Path]:
    root = tmp_path / "scientific" / "core"
    root.mkdir(parents=True, exist_ok=True)
    records_path = root / "nutev_core_records.jsonl"
    records_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    manifest_path = root / "CORE_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "core_type": "NUTEV_CORE_EVIDENCE_BANK",
                "status": "PASS",
                "outputs": {
                    "core_records": {
                        "path": str(records_path),
                        "sha256": _sha(records_path),
                    }
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return records_path, manifest_path


def test_first_core_projection_creates_version_one_under_global_article_id(tmp_path: Path) -> None:
    article_id = _registry_article(tmp_path)
    records, manifest = _write_core(tmp_path, [_core_record()])

    result = project_core_records(
        output_root=tmp_path,
        core_records_path=records,
        core_manifest_path=manifest,
    )

    assert result["status"] == "COMPLETE"
    assert result["created_versions"] == 1
    versions = list_core_versions(output_root=tmp_path, article_id=article_id)
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    assert versions[0]["is_current"] == 1
    assert versions[0]["core_version_id"].startswith("NUTEV-COREV-")


def test_rerun_with_only_generated_at_change_is_idempotent(tmp_path: Path) -> None:
    article_id = _registry_article(tmp_path)
    records, manifest = _write_core(tmp_path, [_core_record()])
    project_core_records(output_root=tmp_path, core_records_path=records, core_manifest_path=manifest)

    records, manifest = _write_core(
        tmp_path,
        [_core_record(generated_at="2026-09-08T12:00:00+00:00")],
    )
    replay = project_core_records(
        output_root=tmp_path,
        core_records_path=records,
        core_manifest_path=manifest,
    )

    assert replay["created_versions"] == 0
    assert replay["matched_current"] == 1
    assert len(list_core_versions(output_root=tmp_path, article_id=article_id)) == 1


def test_new_text_artifact_creates_version_two_and_preserves_version_one(tmp_path: Path) -> None:
    article_id = _registry_article(tmp_path)
    records, manifest = _write_core(tmp_path, [_core_record(text_sha="1" * 64)])
    project_core_records(output_root=tmp_path, core_records_path=records, core_manifest_path=manifest)

    records, manifest = _write_core(tmp_path, [_core_record(text_sha="2" * 64)])
    second = project_core_records(
        output_root=tmp_path,
        core_records_path=records,
        core_manifest_path=manifest,
    )

    assert second["created_versions"] == 1
    versions = list_core_versions(output_root=tmp_path, article_id=article_id)
    assert [row["version_number"] for row in versions] == [1, 2]
    assert [row["is_current"] for row in versions] == [0, 1]
    assert json.loads(versions[0]["input_artifact_hashes_json"])["text_sha256"] == "1" * 64
    assert json.loads(versions[1]["input_artifact_hashes_json"])["text_sha256"] == "2" * 64


def test_replaying_old_core_does_not_roll_back_current_version(tmp_path: Path) -> None:
    article_id = _registry_article(tmp_path)
    old = _core_record(text_sha="1" * 64)
    records, manifest = _write_core(tmp_path, [old])
    project_core_records(output_root=tmp_path, core_records_path=records, core_manifest_path=manifest)
    records, manifest = _write_core(tmp_path, [_core_record(text_sha="2" * 64)])
    project_core_records(output_root=tmp_path, core_records_path=records, core_manifest_path=manifest)

    records, manifest = _write_core(tmp_path, [old])
    replay = project_core_records(
        output_root=tmp_path,
        core_records_path=records,
        core_manifest_path=manifest,
    )

    assert replay["historical_matches"] == 1
    versions = list_core_versions(output_root=tmp_path, article_id=article_id)
    assert [row["is_current"] for row in versions] == [0, 1]


def test_reference_rank_change_alone_does_not_create_scientific_core_version(tmp_path: Path) -> None:
    article_id = _registry_article(tmp_path)
    first = _core_record()
    records, manifest = _write_core(tmp_path, [first])
    project_core_records(output_root=tmp_path, core_records_path=records, core_manifest_path=manifest)

    reranked = deepcopy(first)
    reranked["reference_layer"]["reference_rank"] = 99
    reranked["reference_layer"]["reference_score"] = 2.0
    records, manifest = _write_core(tmp_path, [reranked])
    result = project_core_records(
        output_root=tmp_path,
        core_records_path=records,
        core_manifest_path=manifest,
    )

    assert result["created_versions"] == 0
    assert result["matched_current"] == 1
    assert len(list_core_versions(output_root=tmp_path, article_id=article_id)) == 1


def test_core_without_registry_identity_is_reported_not_guessed(tmp_path: Path) -> None:
    _registry_article(tmp_path)
    unknown = _core_record()
    unknown["identity"]["doi"] = "10.9999/unknown"
    unknown["identity"]["pmid"] = "99999999"
    unknown["identity"]["title"] = "Different unknown article"
    records, manifest = _write_core(tmp_path, [unknown])

    result = project_core_records(
        output_root=tmp_path,
        core_records_path=records,
        core_manifest_path=manifest,
    )

    assert result["status"] == "COMPLETE_WITH_IDENTITY_GAPS"
    assert result["unresolved"] == 1
    connection = sqlite3.connect(tmp_path / "registry" / "article_registry.sqlite")
    try:
        assert connection.execute("SELECT COUNT(*) FROM core_versions").fetchone()[0] == 0
    finally:
        connection.close()


def test_conflicting_core_aliases_do_not_choose_between_articles(tmp_path: Path) -> None:
    registry = SQLiteArticleRegistry(tmp_path / "registry" / "article_registry.sqlite")
    left = registry.register_article(
        {"source_provider": "pubmed", "doi": "10.1000/left-core", "title": "Left"}
    )
    right = registry.register_article(
        {"source_provider": "pubmed", "pmid": "88888888", "title": "Right"}
    )
    assert left.article_id and right.article_id and left.article_id != right.article_id

    core = _core_record()
    core["identity"]["doi"] = "10.1000/left-core"
    core["identity"]["pmid"] = "88888888"
    records, manifest = _write_core(tmp_path, [core])
    result = project_core_records(
        output_root=tmp_path,
        core_records_path=records,
        core_manifest_path=manifest,
    )

    assert result["status"] == "COMPLETE_WITH_IDENTITY_GAPS"
    assert result["identity_conflicts"] == 1
    assert result["created_versions"] == 0


def test_bad_core_hash_blocks_registry_write(tmp_path: Path) -> None:
    article_id = _registry_article(tmp_path)
    records, manifest = _write_core(tmp_path, [_core_record()])
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["outputs"]["core_records"]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    try:
        project_core_records(
            output_root=tmp_path,
            core_records_path=records,
            core_manifest_path=manifest,
        )
    except Exception as exc:
        assert "SHA-256 mismatch" in str(exc)
    else:
        raise AssertionError("projection must fail closed on invalid CORE hash")

    assert list_core_versions(output_root=tmp_path, article_id=article_id) == []


def test_registry_v2_database_migrates_to_core_version_schema_without_losing_article(tmp_path: Path) -> None:
    article_id = _registry_article(tmp_path)
    database = tmp_path / "registry" / "article_registry.sqlite"
    connection = sqlite3.connect(database)
    try:
        connection.execute("DROP TABLE core_versions")
        connection.execute("UPDATE registry_meta SET value='2' WHERE key='schema_version'")
        connection.commit()
    finally:
        connection.close()

    reopened = SQLiteArticleRegistry(database)
    assert reopened.get_article(article_id) is not None
    connection = sqlite3.connect(database)
    try:
        assert connection.execute(
            "SELECT value FROM registry_meta WHERE key='schema_version'"
        ).fetchone()[0] == "3"
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='core_versions'"
        ).fetchone() == ("core_versions",)
    finally:
        connection.close()
