#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
from uuid import uuid4

from argon2 import PasswordHasher

from nutev.registry.migrations import apply_migrations
from nutev.review import HumanReviewEngine, ReviewPolicy, SQLiteHumanReviewStore
from nutev.tenancy import (
    ApplicationService,
    EvidenceLibraryService,
    ExportArtifactInput,
    GlobalEvidenceRegistryReader,
    GlobalRole,
    INTEGRATIVE_REVIEW,
    Principal,
    ProjectExportAuditService,
    ResearchContext,
    SCOPING_REVIEW,
    SQLiteApplicationStore,
    SQLiteAuthProvider,
    SQLiteEvidenceLibraryStore,
    SQLiteProjectExportAuditStore,
    SQLiteSearchOwnershipStore,
    SQLiteWorkspaceProjectStore,
    SearchScopeService,
    WorkspaceProjectService,
    new_opaque_id,
)

REPORT_TYPE = "NUTEV_FULL_MULTITENANT_DEATH_TEST"
REPORT_VERSION = 1


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


def _principal(user_id: str, access: WorkspaceProjectService, *, global_roles=frozenset()) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(access.memberships_for_user(user_id)),
        global_roles=frozenset(global_roles),
        session_id=new_opaque_id("session"),
    )


def _expect_denied(label: str, operation) -> dict[str, str]:
    try:
        operation()
    except (PermissionError, KeyError, FileNotFoundError):
        return {"check": label, "status": "PASS"}
    raise AssertionError(f"{label}: cross-tenant operation unexpectedly succeeded")


def _registry_fixture(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    article_id = "art_shared_tenant_death_001"
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(path) as connection:
        apply_migrations(connection)
        connection.execute(
            """
            INSERT INTO articles(
                article_id, canonical_title, publication_year, journal, abstract,
                created_at, updated_at, first_seen_at, last_seen_at, registry_status
            ) VALUES(?,?,?,?,?,?,?,?,?,'active')
            """,
            (
                article_id,
                "One global document, two private placements",
                2026,
                "NutEV Death Test Journal",
                "Global bibliographic metadata shared by identity only.",
                now,
                now,
                now,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO article_aliases(
                article_id, scheme, normalized_value, raw_value, provider,
                first_seen_at, last_seen_at
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (
                article_id,
                "doi",
                "10.1000/nutev.tenant.death.001",
                "10.1000/nutev.tenant.death.001",
                "fixture",
                now,
                now,
            ),
        )
        connection.commit()
    return article_id


def run_death_test(root: Path) -> dict[str, object]:
    base = Path(root).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    platform_db = base / "platform.sqlite3"
    registry_db = base / "registry" / "article_registry.sqlite"
    export_root = base / "exports"
    checks: list[dict[str, str]] = []

    # Identity + workspace/project boundary.
    auth = SQLiteAuthProvider(platform_db, password_hasher=_fast_hasher())
    user_a = auth.provision_user(
        email="tenant-a@example.org",
        display_name="Tenant A",
        password="tenant A fixture password 123",
    )
    user_b = auth.provision_user(
        email="tenant-b@example.org",
        display_name="Tenant B",
        password="tenant B fixture password 456",
    )
    assert user_a.id != user_b.id
    assert auth.authenticate("tenant-a@example.org", "tenant A fixture password 123") is not None
    assert auth.authenticate("tenant-a@example.org", "wrong password") is None
    checks.append({"check": "identity_separation", "status": "PASS"})

    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(platform_db))
    workspace_a = access.provision_workspace(
        owner_user_id=user_a.id,
        name="Workspace A",
        slug="tenant-a",
    )
    workspace_b = access.provision_workspace(
        owner_user_id=user_b.id,
        name="Workspace B",
        slug="tenant-b",
    )
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)
    project_a = access.create_project(
        principal_a,
        workspace_id=workspace_a.id,
        name="Private Project A",
        slug="private-a",
    )
    project_b = access.create_project(
        principal_b,
        workspace_id=workspace_b.id,
        name="Private Project B",
        slug="private-b",
    )
    context_a = ResearchContext(workspace_a.id, project_a.id)
    context_b = ResearchContext(workspace_b.id, project_b.id)

    selected_a = access.select_context(
        principal_a,
        session_id=principal_a.session_id,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
    )
    selected_b = access.select_context(
        principal_b,
        session_id=principal_b.session_id,
        workspace_id=workspace_b.id,
        project_id=project_b.id,
    )
    assert selected_a.current == context_a
    assert selected_b.current == context_b
    checks.append(
        _expect_denied(
            "context_cross_workspace_denied",
            lambda: access.select_context(
                principal_a,
                session_id=principal_a.session_id,
                workspace_id=workspace_b.id,
                project_id=project_b.id,
            ),
        )
    )

    # Search jobs/runs: exact foreign IDs must remain invisible.
    search_store = SQLiteSearchOwnershipStore(platform_db)
    search = SearchScopeService(search_store, access)
    job_a = f"job_{uuid4().hex}"
    job_b = f"job_{uuid4().hex}"
    search.record_new_job(principal_a, context_a, job_id=job_a)
    search.record_new_job(principal_b, context_b, job_id=job_b)
    search_id_a = "web_tenant_a_death_001"
    search_id_b = "web_tenant_b_death_001"
    search_store.bind_search(job_id=job_a, search_id=search_id_a)
    search_store.bind_search(job_id=job_b, search_id=search_id_b)
    assert search.authorized_search_ids(principal_a, context_a, scope="project") == frozenset({search_id_a})
    assert search.authorized_search_ids(principal_b, context_b, scope="project") == frozenset({search_id_b})
    checks.append(
        _expect_denied(
            "search_idor_denied",
            lambda: search.require_search_access(principal_a, context_a, search_id_b),
        )
    )
    checks.append(
        _expect_denied(
            "search_job_idor_denied",
            lambda: search.require_job_access(principal_b, context_b, job_a),
        )
    )
    assert search_store.owner_for_search("web_unowned_legacy_fixture") is None
    checks.append({"check": "unowned_search_not_adopted", "status": "PASS"})

    # Global identity is shared; placement and full-text access state are private.
    article_id = _registry_fixture(registry_db)
    library = EvidenceLibraryService(
        SQLiteEvidenceLibraryStore(platform_db),
        GlobalEvidenceRegistryReader(registry_db),
        access,
    )
    placement_a = library.save(
        principal_a,
        context_a,
        article_id=article_id,
        scope="project",
        state="included",
        tags=["tenant-a"],
        notes="A private note",
    )
    placement_b = library.save(
        principal_b,
        context_b,
        article_id=article_id,
        scope="project",
        state="background",
        tags=["tenant-b"],
        notes="B private note",
    )
    assert placement_a.document.article_id == placement_b.document.article_id == article_id
    assert placement_a.placement.placement_id != placement_b.placement.placement_id
    assert placement_a.placement.notes == "A private note"
    assert placement_b.placement.notes == "B private note"
    checks.append(
        _expect_denied(
            "placement_idor_denied",
            lambda: library.require_placement(
                principal_a,
                context_a,
                placement_b.placement.placement_id,
            ),
        )
    )
    grant_a = library.create_full_text_grant(
        principal_a,
        context_a,
        article_id=article_id,
        scope="project",
        access_type="retrieved_private_copy",
        license_text="tenant A fixture",
        cache_path="/private/tenant-a/fixture.pdf",
        redistribution_allowed=False,
    )
    assert len(library.full_text_access(principal_a, context_a, article_id)) == 1
    assert library.full_text_access(principal_b, context_b, article_id) == ()
    assert "cache_path" not in grant_a.public_descriptor()
    checks.append({"check": "full_text_grant_isolation", "status": "PASS"})

    # ResearchApplication: same engine/templates, private configuration.
    app_store = SQLiteApplicationStore(platform_db)
    applications = ApplicationService(app_store, access)
    app_a = applications.configure(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        template_id=SCOPING_REVIEW,
        configuration={"research_question": "private A question"},
    )
    app_b = applications.configure(
        principal_b,
        workspace_id=workspace_b.id,
        project_id=project_b.id,
        template_id=INTEGRATIVE_REVIEW,
        configuration={"research_question": "private B question"},
    )
    assert app_a.application.id != app_b.application.id
    assert app_a.configuration()["research_question"] == "private A question"
    assert app_b.configuration()["research_question"] == "private B question"
    checks.append(
        _expect_denied(
            "application_idor_denied",
            lambda: applications.get(
                principal_a,
                workspace_id=workspace_b.id,
                project_id=project_b.id,
            ),
        )
    )

    # Human review: exact foreign round/assignment identifiers fail closed.
    review = HumanReviewEngine(SQLiteHumanReviewStore(platform_db))
    policy = ReviewPolicy(
        decision_options=("include", "exclude"),
        reason_required=True,
        minimum_reviewers_per_item=1,
    )
    round_a = review.create_round(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        project_access_confirmed=True,
        name="Tenant A private review",
        policy=policy,
    )
    round_b = review.create_round(
        principal_b,
        workspace_id=workspace_b.id,
        project_id=project_b.id,
        project_access_confirmed=True,
        name="Tenant B private review",
        policy=policy,
    )
    reviewer_a = review.add_user_reviewer(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        project_access_confirmed=True,
        round_id=round_a.id,
        reviewer_user_id=user_a.id,
        label="A reviewer",
    )
    reviewer_b = review.add_user_reviewer(
        principal_b,
        workspace_id=workspace_b.id,
        project_id=project_b.id,
        project_access_confirmed=True,
        round_id=round_b.id,
        reviewer_user_id=user_b.id,
        label="B reviewer",
    )
    assignment_a = review.assign_item(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        project_access_confirmed=True,
        round_id=round_a.id,
        reviewer_id=reviewer_a.id,
        item_key=article_id,
        payload={"title": "shared title", "private_hint": "A only"},
        allowed_fields=("title",),
    )
    assignment_b = review.assign_item(
        principal_b,
        workspace_id=workspace_b.id,
        project_id=project_b.id,
        project_access_confirmed=True,
        round_id=round_b.id,
        reviewer_id=reviewer_b.id,
        item_key=article_id,
        payload={"title": "shared title", "private_hint": "B only"},
        allowed_fields=("title",),
    )
    access_a = review.access_for_user(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        project_access_confirmed=True,
        round_id=round_a.id,
    )
    payload_a = review.review_payload(access_a)
    assert payload_a["assignments"][0]["payload"] == {"title": "shared title"}
    checks.append(
        _expect_denied(
            "review_round_idor_denied",
            lambda: review.round_summary(
                principal_a,
                workspace_id=workspace_a.id,
                project_id=project_a.id,
                project_access_confirmed=True,
                round_id=round_b.id,
            ),
        )
    )
    checks.append(
        _expect_denied(
            "review_assignment_idor_denied",
            lambda: review.save_decision(
                access_a,
                assignment_id=assignment_b.id,
                decision_value="include",
                reason="must fail",
            ),
        )
    )
    review.save_decision(
        access_a,
        assignment_id=assignment_a.id,
        decision_value="include",
        reason="A reason",
    )
    review.submit(access_a)
    try:
        review.save_decision(
            access_a,
            assignment_id=assignment_a.id,
            decision_value="exclude",
            reason="mutation after lock",
        )
    except ValueError:
        checks.append({"check": "review_submit_lock_immutable", "status": "PASS"})
    else:
        raise AssertionError("submitted review decision was mutable")

    # Export/audit: private artifact custody and exact foreign export ID isolation.
    exports = ProjectExportAuditService(
        SQLiteProjectExportAuditStore(platform_db),
        export_root,
        access,
        applications=app_store,
    )
    export_a = exports.create_export(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        export_kind="DEATH_TEST",
        artifacts=(
            ExportArtifactInput(
                name="tenant-a.txt",
                media_type="text/plain",
                content=b"private export A",
            ),
        ),
    )
    export_b = exports.create_export(
        principal_b,
        workspace_id=workspace_b.id,
        project_id=project_b.id,
        export_kind="DEATH_TEST",
        artifacts=(
            ExportArtifactInput(
                name="tenant-b.txt",
                media_type="text/plain",
                content=b"private export B",
            ),
        ),
    )
    assert export_a.application_id == app_a.application.id
    assert export_b.application_id == app_b.application.id
    assert {item.id for item in exports.list_exports(principal_a, workspace_id=workspace_a.id, project_id=project_a.id)} == {export_a.id}
    assert {item.id for item in exports.list_exports(principal_b, workspace_id=workspace_b.id, project_id=project_b.id)} == {export_b.id}
    checks.append(
        _expect_denied(
            "export_idor_denied",
            lambda: exports.manifest(
                principal_a,
                workspace_id=workspace_a.id,
                project_id=project_a.id,
                export_id=export_b.id,
            ),
        )
    )
    assert exports.audit_chain_valid(principal_a, workspace_id=workspace_a.id, project_id=project_a.id)
    assert exports.audit_chain_valid(principal_b, workspace_id=workspace_b.id, project_id=project_b.id)
    checks.append({"check": "project_audit_chains_independent", "status": "PASS"})

    # A platform administrator with no workspace membership is not a scientific-data bypass.
    platform_admin = Principal(
        user_id=new_opaque_id("user"),
        workspace_memberships=(),
        global_roles=frozenset({GlobalRole.PLATFORM_ADMIN}),
        session_id=new_opaque_id("session"),
    )
    checks.append(
        _expect_denied(
            "platform_admin_search_bypass_denied",
            lambda: search.authorized_search_ids(platform_admin, context_a, scope="project"),
        )
    )
    checks.append(
        _expect_denied(
            "platform_admin_library_bypass_denied",
            lambda: library.list(platform_admin, context_a, scope="project"),
        )
    )
    checks.append(
        _expect_denied(
            "platform_admin_application_bypass_denied",
            lambda: applications.get(
                platform_admin,
                workspace_id=workspace_a.id,
                project_id=project_a.id,
            ),
        )
    )
    checks.append(
        _expect_denied(
            "platform_admin_export_bypass_denied",
            lambda: exports.list_exports(
                platform_admin,
                workspace_id=workspace_a.id,
                project_id=project_a.id,
            ),
        )
    )

    assert all(item["status"] == "PASS" for item in checks)
    return {
        "record_type": REPORT_TYPE,
        "schema_version": REPORT_VERSION,
        "status": "PASS",
        "tenant_count": 2,
        "project_count": 2,
        "shared_global_article_id": article_id,
        "checks_passed": len(checks),
        "checks": checks,
        "assertions": {
            "no_network_required": True,
            "temporary_fixture_only": True,
            "historical_ownership_modified": False,
            "scientific_search_executed": False,
            "article1_state_modified": False,
            "article2_legacy_binding_modified": False,
            "platform_admin_private_bypass": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the hermetic NutEV full multi-tenant death test.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report destination.")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="nutev-multitenant-death-") as tmp:
        report = run_death_test(Path(tmp))
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
