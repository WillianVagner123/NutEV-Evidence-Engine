from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from nutev.tenancy import (
    ExportArtifactInput,
    ExportAuditError,
    GlobalRole,
    Membership,
    Permission,
    Principal,
    ProjectExportAuditService,
    SQLiteApplicationStore,
    SQLiteProjectExportAuditStore,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    WorkspaceRole,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]
WEB_API = ROOT / "apps" / "nutev-web" / "tenant_export_audit_api.py"
ROUTES = ROOT / "apps" / "nutev-web" / "tenant_platform_routes.py"
SCIENCE_EXPORT = ROOT / "src" / "nutev" / "science" / "export.py"


def _principal(user_id: str, access: WorkspaceProjectService, *, global_roles=frozenset()) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(access.memberships_for_user(user_id)),
        global_roles=frozenset(global_roles),
        session_id=new_opaque_id("session"),
    )


def _platform(tmp_path: Path):
    database = tmp_path / "platform.sqlite3"
    export_root = tmp_path / "exports"
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))

    owner_a = new_opaque_id("user")
    owner_b = new_opaque_id("user")
    workspace_a = access.provision_workspace(
        owner_user_id=owner_a,
        name="Workspace A",
        slug="workspace-a",
    )
    workspace_b = access.provision_workspace(
        owner_user_id=owner_b,
        name="Workspace B",
        slug="workspace-b",
    )
    principal_a = _principal(owner_a, access)
    principal_b = _principal(owner_b, access)
    project_a1 = access.create_project(
        principal_a,
        workspace_id=workspace_a.id,
        name="Project A1",
        slug="project-a1",
    )
    project_a2 = access.create_project(
        principal_a,
        workspace_id=workspace_a.id,
        name="Project A2",
        slug="project-a2",
    )
    project_b = access.create_project(
        principal_b,
        workspace_id=workspace_b.id,
        name="Project B",
        slug="project-b",
    )
    applications = SQLiteApplicationStore(database)
    app_a1 = applications.save(
        project_id=project_a1.id,
        application_type="CUSTOM_TEST_REVIEW",
        template_id=None,
        template_version=None,
        config_version="1",
        configuration={"private_question": "A only"},
        actor_user_id=owner_a,
    )
    service = ProjectExportAuditService(
        SQLiteProjectExportAuditStore(database),
        export_root,
        access,
        applications=applications,
    )
    return {
        "database": database,
        "export_root": export_root,
        "access": access,
        "service": service,
        "owner_a": owner_a,
        "owner_b": owner_b,
        "workspace_a": workspace_a,
        "workspace_b": workspace_b,
        "project_a1": project_a1,
        "project_a2": project_a2,
        "project_b": project_b,
        "principal_a": principal_a,
        "principal_b": principal_b,
        "app_a1": app_a1,
    }


def _artifact(name: str = "records.csv", text: str = "id,value\n1,A\n") -> ExportArtifactInput:
    return ExportArtifactInput(name=name, media_type="text/csv", content=text.encode("utf-8"))


def _export(ctx, *, text: str = "id,value\n1,A\n"):
    return ctx["service"].create_export(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a1"].id,
        export_kind="SCIENTIFIC_HANDOFF",
        artifacts=(_artifact(text=text),),
        metadata={"source_sha256": "a" * 64, "purpose": "fixture"},
    )


def test_export_is_project_scoped_hashed_and_application_bound(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    export = _export(ctx)
    assert export.workspace_id == ctx["workspace_a"].id
    assert export.project_id == ctx["project_a1"].id
    assert export.application_id == ctx["app_a1"].application.id

    manifest = ctx["service"].manifest(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a1"].id,
        export_id=export.id,
    )
    assert manifest["application_id"] == ctx["app_a1"].application.id
    assert manifest["assertions"]["tenant_scoped"] is True
    assert manifest["assertions"]["scientific_semantics_inferred"] is False
    assert manifest["artifacts"][0]["sha256"] == sha256(b"id,value\n1,A\n").hexdigest()
    encoded = json.dumps(manifest, sort_keys=True)
    assert str(tmp_path) not in encoded
    assert "relative_path" not in encoded

    stored = (
        ctx["export_root"]
        / ctx["workspace_a"].id
        / ctx["project_a1"].id
        / export.id
        / "records.csv"
    )
    assert stored.read_bytes() == b"id,value\n1,A\n"


def test_exact_foreign_export_id_is_not_visible_cross_tenant(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    export = _export(ctx)
    with pytest.raises((KeyError, PermissionError)):
        ctx["service"].manifest(
            ctx["principal_b"],
            workspace_id=ctx["workspace_b"].id,
            project_id=ctx["project_b"].id,
            export_id=export.id,
        )
    assert ctx["service"].list_exports(
        ctx["principal_b"],
        workspace_id=ctx["workspace_b"].id,
        project_id=ctx["project_b"].id,
    ) == ()


def test_same_workspace_different_projects_are_isolated(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    export = _export(ctx)
    assert ctx["service"].list_exports(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a2"].id,
    ) == ()
    with pytest.raises(KeyError):
        ctx["service"].manifest(
            ctx["principal_a"],
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a2"].id,
            export_id=export.id,
        )


def test_researcher_export_requires_explicit_policy_grant(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    researcher_id = new_opaque_id("user")
    ctx["access"].add_or_update_member(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        user_id=researcher_id,
        role=WorkspaceRole.RESEARCHER,
    )
    researcher = _principal(researcher_id, ctx["access"])
    with pytest.raises(PermissionError):
        ctx["service"].create_export(
            researcher,
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a1"].id,
            export_kind="RESEARCHER_EXPORT",
            artifacts=(_artifact(),),
        )
    exported = ctx["service"].create_export(
        researcher,
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a1"].id,
        export_kind="RESEARCHER_EXPORT",
        artifacts=(_artifact(),),
        policy_grants=frozenset({Permission.EXPORT}),
    )
    assert exported.created_by == researcher_id


def test_viewer_can_audit_but_cannot_export_without_policy(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    _export(ctx)
    viewer_id = new_opaque_id("user")
    ctx["access"].add_or_update_member(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        user_id=viewer_id,
        role=WorkspaceRole.VIEWER,
    )
    viewer = _principal(viewer_id, ctx["access"])
    assert len(ctx["service"].list_exports(
        viewer,
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a1"].id,
    )) == 1
    assert ctx["service"].audit_chain_valid(
        viewer,
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a1"].id,
    )
    with pytest.raises(PermissionError):
        ctx["service"].create_export(
            viewer,
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a1"].id,
            export_kind="VIEWER_EXPORT",
            artifacts=(_artifact(),),
        )


def test_reviewer_has_no_project_export_or_audit_surface(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    reviewer_id = new_opaque_id("user")
    ctx["access"].add_or_update_member(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        user_id=reviewer_id,
        role=WorkspaceRole.REVIEWER,
    )
    reviewer = _principal(reviewer_id, ctx["access"])
    with pytest.raises(PermissionError):
        ctx["service"].list_exports(
            reviewer,
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a1"].id,
        )
    with pytest.raises(PermissionError):
        ctx["service"].create_export(
            reviewer,
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a1"].id,
            export_kind="REVIEWER_EXPORT",
            artifacts=(_artifact(),),
        )


def test_platform_admin_is_not_private_export_bypass(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    platform_user = new_opaque_id("user")
    platform_admin = Principal(
        user_id=platform_user,
        workspace_memberships=(),
        global_roles=frozenset({GlobalRole.PLATFORM_ADMIN}),
        session_id=new_opaque_id("session"),
    )
    with pytest.raises(PermissionError):
        ctx["service"].list_exports(
            platform_admin,
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a1"].id,
        )
    with pytest.raises(PermissionError):
        ctx["service"].create_export(
            platform_admin,
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a1"].id,
            export_kind="ADMIN_BYPASS",
            artifacts=(_artifact(),),
        )


def test_artifact_content_is_not_copied_into_platform_database(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    secret = "UNIQUE_PRIVATE_EXPORT_BODY_87f4a9b2"
    _export(ctx, text=secret)
    raw = ctx["database"].read_bytes()
    assert secret.encode("utf-8") not in raw


def test_tampered_artifact_fails_hash_verification(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    export = _export(ctx)
    path = (
        ctx["export_root"]
        / ctx["workspace_a"].id
        / ctx["project_a1"].id
        / export.id
        / "records.csv"
    )
    path.write_text("tampered", encoding="utf-8")
    with pytest.raises(ExportAuditError, match="integrity mismatch"):
        ctx["service"].read_artifact(
            ctx["principal_a"],
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a1"].id,
            export_id=export.id,
            name="records.csv",
        )


def test_audit_chain_detects_database_tampering(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    export = _export(ctx)
    ctx["service"].read_artifact(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a1"].id,
        export_id=export.id,
        name="records.csv",
    )
    assert ctx["service"].audit_chain_valid(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a1"].id,
    )
    with sqlite3.connect(ctx["database"]) as connection:
        connection.execute(
            "UPDATE platform_project_audit_events SET details_json = ? WHERE seq = (SELECT MIN(seq) FROM platform_project_audit_events)",
            ('{"tampered":true}',),
        )
        connection.commit()
    assert not ctx["service"].audit_chain_valid(
        ctx["principal_a"],
        workspace_id=ctx["workspace_a"].id,
        project_id=ctx["project_a1"].id,
    )


@pytest.mark.parametrize("name", ["../secret.txt", "folder/file.txt", "folder\\file.txt", ".", ".."])
def test_artifact_name_cannot_escape_export_directory(tmp_path: Path, name: str) -> None:
    _platform(tmp_path)
    with pytest.raises(ValueError, match="artifact name"):
        ExportArtifactInput(name=name, media_type="text/plain", content=b"x")


def test_duplicate_artifact_names_are_rejected(tmp_path: Path) -> None:
    ctx = _platform(tmp_path)
    with pytest.raises(ValueError, match="duplicate"):
        ctx["service"].create_export(
            ctx["principal_a"],
            workspace_id=ctx["workspace_a"].id,
            project_id=ctx["project_a1"].id,
            export_kind="DUPLICATE",
            artifacts=(
                ExportArtifactInput(name="same.txt", media_type="text/plain", content=b"a"),
                ExportArtifactInput(name="same.txt", media_type="text/plain", content=b"b"),
            ),
        )


def test_http_contract_derives_scope_and_accepts_no_source_path_or_identity() -> None:
    source = WEB_API.read_text(encoding="utf-8")
    assert '"workspace_id"' in source
    assert '"project_id"' in source
    assert '"application_id"' in source
    assert "_tenant_search_session" in source
    assert "project_context_required" in source
    assert "content_text" in source
    assert "content_base64" in source
    assert '"path"' in source
    assert "policy_grants" not in source
    assert "NUTEV_EXPORT_ROOT" in source
    assert "X-Content-Type-Options" in source
    assert "private, no-store" in source


def test_platform_route_installs_export_audit_without_touching_scientific_exporter() -> None:
    routes = ROUTES.read_text(encoding="utf-8")
    assert "install_export_audit_routes" in routes
    scientific = SCIENCE_EXPORT.read_text(encoding="utf-8")
    assert "ProjectExportAuditService" not in scientific
    assert "workspace_id" not in scientific
    assert "Permission.PROJECT_AUDIT_READ" not in scientific
