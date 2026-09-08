from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from nutev.applications.willian_doctorate_a2 import (
    A2ConfigurationError,
    A2IntegrativeService,
    LegacyBindingEvidence,
    load_a2_config,
)
from nutev.tenancy import (
    GlobalRole,
    Membership,
    PermissionDenied,
    Principal,
    WorkspaceRole,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]


def _principal(
    role: WorkspaceRole = WorkspaceRole.WORKSPACE_OWNER,
    *,
    workspace_id: str | None = None,
    user_id: str | None = None,
    global_roles: frozenset[GlobalRole] = frozenset(),
) -> tuple[Principal, str, str, str]:
    uid = user_id or new_opaque_id("user")
    wid = workspace_id or new_opaque_id("workspace")
    project_id = new_opaque_id("project")
    application_id = new_opaque_id("application")
    return (
        Principal(
            user_id=uid,
            workspace_memberships=(Membership(workspace_id=wid, user_id=uid, role=role),),
            global_roles=global_roles,
            session_id=new_opaque_id("session"),
        ),
        wid,
        project_id,
        application_id,
    )


def _service(tmp_path: Path) -> A2IntegrativeService:
    return A2IntegrativeService(
        repo_root=ROOT,
        database_path=tmp_path / "platform" / "auth.sqlite3",
    )


def _binding(**overrides) -> LegacyBindingEvidence:
    payload = {
        "manifest_sha256": "a" * 64,
        "target_key": "article2_project",
        "classification": "ARTICLE2_PRIVATE",
        "record_count": 7,
        "source_fingerprints": ("b" * 64, "c" * 64),
        "evidence": "Reviewed migration manifest proves this material belongs to the Article 2 project.",
        "validation_status": "VALIDATED",
    }
    payload.update(overrides)
    return LegacyBindingEvidence(**payload)


def test_article2_config_is_integrative_and_starts_fail_closed() -> None:
    config = load_a2_config(ROOT)
    assert config.assembly_id == "WILLIAN_DOCTORATE_A2"
    assert config.application_template == "INTEGRATIVE_REVIEW"
    assert config.workflow_type == "INTEGRATIVE_REVIEW"
    assert config.phases[0] == "LEGACY_BINDING"
    assert config.phases[-1] == "COMPLETE"
    assert config.legacy_binding_required is True
    assert config.legacy_target_key == "article2_project"
    assert config.legacy_classification == "ARTICLE2_PRIVATE"
    assert config.legacy_initial_state == "REQUIRED_UNMATERIALIZED"
    assert all(config.guardrails.values())


def test_bootstrap_is_blocked_and_cannot_advance_without_validated_legacy_binding(tmp_path: Path) -> None:
    service = _service(tmp_path)
    owner, workspace_id, project_id, application_id = _principal()
    state = service.bootstrap(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
    )
    assert state.current_phase == "LEGACY_BINDING"
    assert state.workflow_status == "BLOCKED"
    assert state.legacy_binding_state == "REQUIRED_UNMATERIALIZED"
    assert state.legacy_binding_fingerprint is None

    status = service.status(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
    )
    assert status["blocked_reason"] == "LEGACY_BINDING_REQUIRED"
    assert status["can_advance"] is False
    assert all(value is False for value in status["scientific_side_effects"].values())

    with pytest.raises(ValueError, match="LEGACY_BINDING_REQUIRED"):
        service.advance(
            owner,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            project_access_confirmed=True,
            next_phase="SEARCH_STRATEGY",
            evidence="should not bypass binding",
        )


def test_binding_evidence_rejects_wrong_target_classification_hashes_and_status() -> None:
    with pytest.raises(A2ConfigurationError, match="target"):
        _binding(target_key="article1_project")
    with pytest.raises(A2ConfigurationError, match="classification"):
        _binding(classification="ARTICLE1_PRIVATE")
    with pytest.raises(A2ConfigurationError, match="SHA-256"):
        _binding(manifest_sha256="not-a-hash")
    with pytest.raises(A2ConfigurationError, match="unique"):
        _binding(source_fingerprints=("b" * 64, "b" * 64))
    with pytest.raises(A2ConfigurationError, match="VALIDATED"):
        _binding(validation_status="DRY_RUN_REVIEW_REQUIRED")
    with pytest.raises(A2ConfigurationError, match="positive"):
        _binding(record_count=0)


def test_valid_internal_binding_activates_workflow_without_copying_scientific_state(tmp_path: Path) -> None:
    service = _service(tmp_path)
    owner, workspace_id, project_id, application_id = _principal()
    state = service.bootstrap(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
    )
    bound = service.register_legacy_binding(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
        evidence=_binding(),
    )
    assert bound.workflow_id == state.workflow_id
    assert bound.current_phase == "SEARCH_STRATEGY"
    assert bound.workflow_status == "ACTIVE"
    assert bound.legacy_binding_state == "READY"
    assert bound.legacy_binding_fingerprint is not None
    assert len(bound.legacy_binding_fingerprint) == 64

    with sqlite3.connect(service.store.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'article2_integrative_%'"
            )
        }
        columns = {
            row[1].casefold()
            for table in tables
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
    assert tables >= {"article2_integrative_workflows", "article2_integrative_events"}
    forbidden_columns = {
        "query",
        "query_text",
        "search_id",
        "search_run_id",
        "source_path",
        "file_path",
        "document_body",
        "abstract",
        "full_text",
        "article1_project_id",
    }
    assert forbidden_columns.isdisjoint(columns)

    status = service.status(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
    )
    assert all(value is False for value in status["scientific_side_effects"].values())


def test_phases_advance_only_in_configured_order_with_hashed_evidence(tmp_path: Path) -> None:
    service = _service(tmp_path)
    owner, workspace_id, project_id, application_id = _principal()
    service.bootstrap(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
    )
    service.register_legacy_binding(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
        evidence=_binding(),
    )

    with pytest.raises(ValueError, match="next phase must be SEARCH_EXECUTION"):
        service.advance(
            owner,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            project_access_confirmed=True,
            next_phase="DEDUPLICATION",
            evidence="attempted phase skip",
        )
    with pytest.raises(ValueError, match="requires evidence"):
        service.advance(
            owner,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            project_access_confirmed=True,
            next_phase="SEARCH_EXECUTION",
            evidence="",
        )

    evidence = "Reviewed strategy/version checkpoint, not raw scientific content."
    state = service.advance(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
        next_phase="SEARCH_EXECUTION",
        evidence=evidence,
    )
    assert state.current_phase == "SEARCH_EXECUTION"
    events = service.events(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        application_id=application_id,
        project_access_confirmed=True,
    )
    event = events[-1]
    assert event["phase"] == "SEARCH_EXECUTION"
    assert event["evidence_sha256"] is not None
    assert evidence not in repr(events)


def test_workflows_are_project_isolated_even_inside_same_workspace(tmp_path: Path) -> None:
    service = _service(tmp_path)
    owner, workspace_id, project_a, app_a = _principal()
    project_b, app_b = new_opaque_id("project"), new_opaque_id("application")
    state_a = service.bootstrap(
        owner,
        workspace_id=workspace_id,
        project_id=project_a,
        application_id=app_a,
        project_access_confirmed=True,
    )
    state_b = service.bootstrap(
        owner,
        workspace_id=workspace_id,
        project_id=project_b,
        application_id=app_b,
        project_access_confirmed=True,
    )
    assert state_a.workflow_id != state_b.workflow_id

    service.register_legacy_binding(
        owner,
        workspace_id=workspace_id,
        project_id=project_a,
        application_id=app_a,
        project_access_confirmed=True,
        evidence=_binding(),
    )
    assert service.status(
        owner,
        workspace_id=workspace_id,
        project_id=project_a,
        application_id=app_a,
        project_access_confirmed=True,
    )["legacy_binding_state"] == "READY"
    assert service.status(
        owner,
        workspace_id=workspace_id,
        project_id=project_b,
        application_id=app_b,
        project_access_confirmed=True,
    )["legacy_binding_state"] == "REQUIRED_UNMATERIALIZED"

    with pytest.raises(FileNotFoundError):
        service.status(
            owner,
            workspace_id=workspace_id,
            project_id=project_b,
            application_id=app_a,
            project_access_confirmed=True,
        )


def test_platform_admin_does_not_bypass_article2_application_manage(tmp_path: Path) -> None:
    service = _service(tmp_path)
    viewer, workspace_id, project_id, application_id = _principal(
        WorkspaceRole.VIEWER,
        global_roles=frozenset({GlobalRole.PLATFORM_ADMIN}),
    )
    with pytest.raises(PermissionDenied):
        service.bootstrap(
            viewer,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            project_access_confirmed=True,
        )
