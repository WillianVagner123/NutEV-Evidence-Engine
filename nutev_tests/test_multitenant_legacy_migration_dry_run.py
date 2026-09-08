from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from nutev.migration import (
    MappingRule,
    OwnershipClass,
    run_legacy_multitenant_dry_run,
)
from nutev.migration.profiles import build_willian_doctorate_plan

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "plan_multitenant_legacy_migration.py"


def _write(path: Path, content: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _mapping(path: Path, rules: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "rules": rules}), encoding="utf-8")
    return path


def test_reference_only_dry_run_maps_known_a1_and_explicit_a2_without_mutation(tmp_path: Path) -> None:
    source = tmp_path / "project_output_reference"
    a1_context = source / "agent_context" / "article1" / "SEARCH_STATE.json"
    a1_review = source / "scientific" / "review_routes" / "search_001" / "article1" / "gold.json"
    validation = source / "16_validation_server" / "validation.sqlite3"
    a2_state = source / "reviewed_article2_runtime" / "state.json"
    legacy_owner = source / "15_web_searches" / ".ownership.json"
    _write(a1_context, '{"state":"preserve"}')
    _write(a1_review, '{"decision":"human"}')
    _write(validation, b"sqlite-fixture-do-not-open")
    _write(a2_state, '{"article2":"explicit"}')
    _write(legacy_owner, '{}')

    originals = {path: _hash(path) for path in (a1_context, a1_review, validation, a2_state, legacy_owner)}
    mapping_path = _mapping(
        tmp_path / "mapping.json",
        [
            {
                "pattern": "reviewed_article2_runtime/*",
                "classification": "ARTICLE2_PRIVATE",
                "target_key": "article2_project",
                "evidence": "operator-reviewed runtime manifest proves these files belong to Article 2",
            }
        ],
    )
    report_path = tmp_path / "LEGACY_MIGRATION_MANIFEST.json"
    report = run_legacy_multitenant_dry_run(
        plan=build_willian_doctorate_plan(),
        source_roots=[source],
        report_path=report_path,
        explicit_mapping_path=mapping_path,
    )

    assert report["status"] == "DRY_RUN_PASS"
    assert report["activation_supported"] is False
    assert report["mutation_policy"] == {
        "source_files_written": False,
        "platform_database_written": False,
        "searches_executed": False,
        "scientific_results_recomputed": False,
        "human_decisions_changed": False,
        "prisma_recreated": False,
    }
    assert report["counts"]["by_target"]["article1_project"] == 2
    assert report["counts"]["by_target"]["article2_project"] == 1
    assert report["counts"]["by_target"]["doctorate_workspace"] == 1
    assert report["counts"]["by_classification"]["SYSTEM"] == 1
    assert report["counts"]["by_classification"]["UNKNOWN"] == 0
    assert report["counts"]["symlinks_seen"] == 0
    assert report["blockers"] == []
    assert all(record["source_unchanged"] is True for record in report["records"])
    assert all(record["source_sha256_before"] == record["source_sha256_after"] for record in report["records"])
    assert {path: _hash(path) for path in originals} == originals
    assert report_path.is_file()
    assert not (source / "LEGACY_MIGRATION_MANIFEST.json").exists()

    targets = {item["key"]: item for item in report["logical_targets"]}
    assert targets["article1_project"]["application_template"] == "SCOPING_REVIEW"
    assert targets["article2_project"]["application_template"] == "INTEGRATIVE_REVIEW"
    assert all(item["activation_id"] is None for item in targets.values())
    assert report["owner"]["activation_user_id"] is None


def test_article2_is_not_inferred_when_runtime_mapping_is_missing(tmp_path: Path) -> None:
    source = tmp_path / "project_output_reference"
    _write(source / "agent_context" / "article1" / "CONTEXT_MANIFEST.json", "{}")
    report = run_legacy_multitenant_dry_run(
        plan=build_willian_doctorate_plan(),
        source_roots=[source],
        report_path=tmp_path / "manifest.json",
    )
    assert report["status"] == "DRY_RUN_REVIEW_REQUIRED"
    assert report["counts"]["by_target"]["article1_project"] == 1
    assert report["counts"]["by_target"]["article2_project"] == 0
    assert any(
        item["code"] == "REQUIRED_TARGET_NOT_MATERIALIZED" and "article2_project" in item["detail"]
        for item in report["blockers"]
    )


def test_unknown_files_never_receive_private_target_or_reference_action(tmp_path: Path) -> None:
    source = tmp_path / "project_output_reference"
    unknown = source / "bank" / "searches" / "mystery" / "result.json"
    _write(unknown, '{"query":"ownership unknown"}')
    report = run_legacy_multitenant_dry_run(
        plan=build_willian_doctorate_plan(),
        source_roots=[source],
        report_path=tmp_path / "manifest.json",
    )
    record = next(item for item in report["records"] if item["relative_path"].endswith("result.json"))
    assert record["classification"] == "UNKNOWN"
    assert record["logical_target_key"] is None
    assert record["migration_action"] == "NO_AUTOMATIC_MIGRATION"
    assert report["guardrails"]["unknown_never_auto_migrated"] is True
    assert report["status"] == "DRY_RUN_REVIEW_REQUIRED"


def test_conflicting_explicit_rule_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "project_output_reference"
    _write(source / "agent_context" / "article1" / "SEARCH_STATE.json", "{}")
    mapping_path = _mapping(
        tmp_path / "mapping.json",
        [
            {
                "pattern": "agent_context/article1/*",
                "classification": "ARTICLE2_PRIVATE",
                "target_key": "article2_project",
                "evidence": "deliberately contradictory fixture",
            }
        ],
    )
    report = run_legacy_multitenant_dry_run(
        plan=build_willian_doctorate_plan(),
        source_roots=[source],
        report_path=tmp_path / "manifest.json",
        explicit_mapping_path=mapping_path,
    )
    assert report["status"] == "DRY_RUN_FAIL"
    assert report["counts"]["mapping_conflicts"] == 1
    record = report["records"][0]
    assert record["classification"] == "UNKNOWN"
    assert record["logical_target_key"] is None
    assert record["mapping_source"] == "conflict"


def test_report_destination_inside_legacy_root_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "project_output_reference"
    _write(source / "agent_context" / "article1" / "SEARCH_STATE.json", "{}")
    with pytest.raises(ValueError, match="outside every legacy source root"):
        run_legacy_multitenant_dry_run(
            plan=build_willian_doctorate_plan(),
            source_roots=[source],
            report_path=source / "LEGACY_MIGRATION_MANIFEST.json",
        )


def test_explicit_mapping_inside_legacy_root_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "project_output_reference"
    _write(source / "agent_context" / "article1" / "SEARCH_STATE.json", "{}")
    mapping_path = _mapping(
        source / "control" / "mapping.json",
        [
            {
                "pattern": "agent_context/article1/*",
                "classification": "ARTICLE1_PRIVATE",
                "target_key": "article1_project",
                "evidence": "fixture control mapping",
            }
        ],
    )
    with pytest.raises(ValueError, match="explicit mapping must be outside"):
        run_legacy_multitenant_dry_run(
            plan=build_willian_doctorate_plan(),
            source_roots=[source],
            report_path=tmp_path / "manifest.json",
            explicit_mapping_path=mapping_path,
        )


def test_symlink_is_recorded_not_followed_and_blocks_pass(tmp_path: Path) -> None:
    source = tmp_path / "project_output_reference"
    target = tmp_path / "outside-secret.txt"
    link = source / "agent_context" / "article1" / "external-link.txt"
    _write(source / "agent_context" / "article1" / "SEARCH_STATE.json", "{}")
    _write(target, "outside bytes must never be followed")
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation unavailable on this platform")

    target_before = _hash(target)
    report = run_legacy_multitenant_dry_run(
        plan=build_willian_doctorate_plan(),
        source_roots=[source],
        report_path=tmp_path / "manifest.json",
    )

    assert report["status"] == "DRY_RUN_REVIEW_REQUIRED"
    assert report["counts"]["symlinks_seen"] == 1
    assert report["symlinks"] == [
        {
            "source_root": str(source.resolve()),
            "relative_path": "agent_context/article1/external-link.txt",
            "followed": "false",
            "migration_action": "NO_AUTOMATIC_MIGRATION",
        }
    ]
    assert any(item["code"] == "SYMLINK_NOT_FOLLOWED" for item in report["blockers"])
    assert report["guardrails"]["symlinks_never_followed_or_auto_migrated"] is True
    assert _hash(target) == target_before
    assert all(record["relative_path"] != "agent_context/article1/external-link.txt" for record in report["records"])


def test_explicit_mapping_requires_evidence_and_safe_relative_pattern() -> None:
    with pytest.raises(ValueError, match="explicit evidence"):
        MappingRule(
            pattern="article2/*",
            classification=OwnershipClass.ARTICLE2_PRIVATE,
            target_key="article2_project",
            evidence="",
        )
    with pytest.raises(ValueError, match="safe relative"):
        MappingRule(
            pattern="../other-tenant/*",
            classification=OwnershipClass.ARTICLE2_PRIVATE,
            target_key="article2_project",
            evidence="bad traversal fixture",
        )


def test_generic_planner_has_inventory_vocabulary_but_not_first_party_target_labels() -> None:
    source = (ROOT / "src" / "nutev" / "migration" / "legacy_plan.py").read_text(encoding="utf-8").casefold()
    # PR-0 ownership vocabulary is intentionally generic input to the migration planner,
    # including WILLIAN_PRIVATE / ARTICLE1_PRIVATE / ARTICLE2_PRIVATE. What must stay outside
    # this module are the concrete customer hierarchy, labels, paths and target keys.
    assert "doutorado willian" not in source
    assert "artigo 1" not in source
    assert "artigo 2" not in source
    assert "agent_context/article1" not in source
    assert "scientific/review_routes" not in source
    assert "article1_project" not in source
    assert "article2_project" not in source
    assert "doctorate_workspace" not in source


def test_cli_requires_dry_run_and_has_no_activation_flag() -> None:
    completed = subprocess.run(
        [sys.executable, str(TOOL)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 2
    assert "activation is not implemented" in completed.stderr
    tool_source = TOOL.read_text(encoding="utf-8")
    assert '"--activate"' not in tool_source
    assert '"--apply"' not in tool_source
    assert "SQLiteApplicationStore" not in tool_source
    assert "SQLiteWorkspaceProjectStore" not in tool_source


def test_source_not_materialized_is_explicit_not_false_success(tmp_path: Path) -> None:
    report = run_legacy_multitenant_dry_run(
        plan=build_willian_doctorate_plan(),
        source_roots=[tmp_path / "missing-output"],
        report_path=tmp_path / "manifest.json",
    )
    assert report["status"] == "SOURCE_NOT_MATERIALIZED"
    assert report["counts"]["files_seen"] == 0
    assert report["counts"]["symlinks_seen"] == 0
    assert report["activation_supported"] is False
