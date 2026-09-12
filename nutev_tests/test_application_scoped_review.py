from __future__ import annotations

from argon2 import PasswordHasher

from nutev.review import HumanReviewEngine, ReviewPolicy, SQLiteHumanReviewStore
from nutev.review.application_scope import (
    ApplicationScopedReviewService,
    SQLiteReviewApplicationBindingStore,
)
from nutev.tenancy import (
    ApplicationService,
    GENERIC_EVIDENCE_PROJECT,
    Principal,
    SCOPING_REVIEW,
    SQLiteApplicationStore,
    SQLiteAuthProvider,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    new_opaque_id,
)


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


def _principal(user_id: str, access: WorkspaceProjectService) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(access.memberships_for_user(user_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )


def _fixture(tmp_path):
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user = auth.provision_user(
        email="review-owner@example.org",
        display_name="Review Owner",
        password="review owner password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(
        owner_user_id=user.id,
        name="Review Workspace",
        slug="review-workspace",
    )
    principal = _principal(user.id, access)
    project_a = access.create_project(
        principal,
        workspace_id=workspace.id,
        name="Project A",
        slug="review-project-a",
    )
    project_b = access.create_project(
        principal,
        workspace_id=workspace.id,
        name="Project B",
        slug="review-project-b",
    )
    applications = ApplicationService(SQLiteApplicationStore(database), access)
    app_a = applications.configure(
        principal,
        workspace_id=workspace.id,
        project_id=project_a.id,
        template_id=SCOPING_REVIEW,
    )
    app_b = applications.configure(
        principal,
        workspace_id=workspace.id,
        project_id=project_b.id,
        template_id=GENERIC_EVIDENCE_PROJECT,
    )
    engine = HumanReviewEngine(SQLiteHumanReviewStore(database))
    bindings = SQLiteReviewApplicationBindingStore(database)
    service = ApplicationScopedReviewService(engine, applications, bindings)
    return principal, workspace, project_a, project_b, app_a, app_b, engine, bindings, service


def test_generic_review_lists_only_explicitly_application_bound_rounds(tmp_path) -> None:
    principal, workspace, project_a, _project_b, app_a, _app_b, engine, bindings, service = _fixture(tmp_path)

    legacy_unbound = engine.create_round(
        principal,
        workspace_id=workspace.id,
        project_id=project_a.id,
        project_access_confirmed=True,
        name="Historical unbound round",
        policy=ReviewPolicy(decision_options=("Y", "N")),
    )
    created = service.create_round(
        principal,
        workspace_id=workspace.id,
        project_id=project_a.id,
        name="Application-bound round",
        policy=ReviewPolicy(
            decision_options=("include", "exclude", "uncertain"),
            minimum_reviewers_per_item=2,
        ),
    )

    overview = service.overview(
        principal,
        workspace_id=workspace.id,
        project_id=project_a.id,
    )
    assert overview["application"]["id"] == app_a.application.id
    assert overview["legacy_unbound_rounds_visible"] is False
    assert overview["scientific_decisions_automatic"] is False
    assert [item["id"] for item in overview["rounds"]] == [created["id"]]
    assert legacy_unbound.id not in repr(overview)
    assert bindings.get(created["id"]).application_id == app_a.application.id
    assert bindings.get(legacy_unbound.id) is None


def test_application_review_binding_is_project_isolated(tmp_path) -> None:
    principal, workspace, project_a, project_b, app_a, app_b, _engine, _bindings, service = _fixture(tmp_path)

    round_a = service.create_round(
        principal,
        workspace_id=workspace.id,
        project_id=project_a.id,
        name="Round A",
        policy=ReviewPolicy(decision_options=("yes", "no")),
    )
    round_b = service.create_round(
        principal,
        workspace_id=workspace.id,
        project_id=project_b.id,
        name="Round B",
        policy=ReviewPolicy(decision_options=("keep", "drop")),
    )

    overview_a = service.overview(principal, workspace_id=workspace.id, project_id=project_a.id)
    overview_b = service.overview(principal, workspace_id=workspace.id, project_id=project_b.id)
    assert overview_a["application"]["id"] == app_a.application.id
    assert overview_b["application"]["id"] == app_b.application.id
    assert [item["id"] for item in overview_a["rounds"]] == [round_a["id"]]
    assert [item["id"] for item in overview_b["rounds"]] == [round_b["id"]]

    try:
        service.round_summary(
            principal,
            workspace_id=workspace.id,
            project_id=project_b.id,
            round_id=round_a["id"],
        )
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("cross-project application review round must fail closed")


def test_review_requires_an_active_research_application(tmp_path) -> None:
    database = tmp_path / "no-application.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user = auth.provision_user(
        email="no-app@example.org",
        display_name="No Application",
        password="no application password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(owner_user_id=user.id, name="Workspace", slug="no-app")
    principal = _principal(user.id, access)
    project = access.create_project(
        principal,
        workspace_id=workspace.id,
        name="Project",
        slug="project",
    )
    applications = ApplicationService(SQLiteApplicationStore(database), access)
    service = ApplicationScopedReviewService(
        HumanReviewEngine(SQLiteHumanReviewStore(database)),
        applications,
        SQLiteReviewApplicationBindingStore(database),
    )

    try:
        service.overview(principal, workspace_id=workspace.id, project_id=project.id)
    except LookupError as exc:
        assert str(exc) == "review_application_required"
    else:
        raise AssertionError("generic Review must require an explicit ResearchApplication")
