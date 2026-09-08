from __future__ import annotations

from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from argon2 import PasswordHasher
import pytest

from nutev.tenancy import (
    ApplicationService,
    ApplicationTemplate,
    ApplicationTemplateCatalog,
    GENERIC_EVIDENCE_PROJECT,
    INTEGRATIVE_REVIEW,
    Permission,
    Principal,
    SCOPING_REVIEW,
    SQLiteApplicationStore,
    SQLiteAuthProvider,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    WorkspaceRole,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


def _principal(user_id: str, access: WorkspaceProjectService) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(access.memberships_for_user(user_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )


def _fixture(tmp_path: Path):
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user_a = auth.provision_user(
        email="app-a@example.org",
        display_name="Application A",
        password="application a password is sufficiently long",
    )
    user_b = auth.provision_user(
        email="app-b@example.org",
        display_name="Application B",
        password="application b password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace_a = access.provision_workspace(owner_user_id=user_a.id, name="Workspace A", slug="app-a")
    workspace_b = access.provision_workspace(owner_user_id=user_b.id, name="Workspace B", slug="app-b")
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)
    project_a = access.create_project(
        principal_a,
        workspace_id=workspace_a.id,
        name="Project A",
        slug="project-a",
    )
    project_b = access.create_project(
        principal_b,
        workspace_id=workspace_b.id,
        name="Project B",
        slug="project-b",
    )
    service = ApplicationService(SQLiteApplicationStore(database), access)
    return (
        database,
        auth,
        access,
        service,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    )


def test_builtin_templates_are_small_reusable_and_free_of_private_project_state() -> None:
    catalog = ApplicationTemplateCatalog()
    templates = {template.template_id: template for template in catalog.list()}

    assert set(templates) == {
        GENERIC_EVIDENCE_PROJECT,
        SCOPING_REVIEW,
        INTEGRATIVE_REVIEW,
    }
    scoping = templates[SCOPING_REVIEW]
    assert scoping.components == (
        "PCC",
        "SEARCH",
        "DEDUPLICATION",
        "TITLE_ABSTRACT_SCREENING",
        "FULL_TEXT",
        "EXTRACTION",
        "HUMAN_VERIFICATION",
        "SYNTHESIS",
        "PRISMA_SCR",
    )
    encoded = json.dumps([template.descriptor() for template in templates.values()]).casefold()
    for forbidden in (
        "willian",
        "artigo 1",
        "artigo 2",
        "d-132",
        "abcd-nutev",
        "private_notes",
        "screening_decision",
        "research_question_value",
    ):
        assert forbidden not in encoded


def test_same_template_yields_independent_private_project_configuration(tmp_path: Path) -> None:
    (
        _database,
        _auth,
        access,
        service,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _fixture(tmp_path)
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)

    app_a = service.configure(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        template_id=SCOPING_REVIEW,
        config_version="a-1",
        configuration={"research_question": "A private question", "local_policy": "A-only"},
    )
    app_b = service.configure(
        principal_b,
        workspace_id=workspace_b.id,
        project_id=project_b.id,
        template_id=SCOPING_REVIEW,
        config_version="b-1",
        configuration={"research_question": "B private question", "local_policy": "B-only"},
    )

    assert app_a.application.template_id == app_b.application.template_id == SCOPING_REVIEW
    assert app_a.application.id != app_b.application.id
    assert app_a.configuration()["research_question"] == "A private question"
    assert app_b.configuration()["research_question"] == "B private question"
    assert "B private question" not in json.dumps(app_a.descriptor())
    assert "A private question" not in json.dumps(app_b.descriptor())

    template = service.catalog.get(SCOPING_REVIEW)
    assert template is not None
    assert "research_question" not in template.defaults()
    assert "A private question" not in json.dumps(template.descriptor())
    assert "B private question" not in json.dumps(template.descriptor())


def test_custom_application_type_is_not_blocked_by_closed_enum(tmp_path: Path) -> None:
    (
        _database,
        _auth,
        access,
        service,
        user_a,
        _user_b,
        workspace_a,
        _workspace_b,
        project_a,
        _project_b,
    ) = _fixture(tmp_path)
    principal = _principal(user_a.id, access)
    instance = service.configure(
        principal,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        application_type="CUSTOM_EVIDENCE_WORKFLOW_2030",
        config_version="1",
        configuration={"components": ["SEARCH", "CUSTOM_STEP", "SYNTHESIS"]},
    )
    assert instance.application.application_type == "CUSTOM_EVIDENCE_WORKFLOW_2030"
    assert instance.application.template_id is None
    assert instance.configuration()["components"] == ["SEARCH", "CUSTOM_STEP", "SYNTHESIS"]


def test_template_catalog_accepts_injected_future_template_without_engine_change() -> None:
    future = ApplicationTemplate(
        template_id="RAPID_REVIEW_2030",
        version="2.0",
        name="Rapid Review 2030",
        application_type="RAPID_REVIEW",
        components=("SEARCH", "SCREEN", "SYNTHESIS"),
    )
    catalog = ApplicationTemplateCatalog([future])
    assert catalog.get("RAPID_REVIEW_2030", "2.0") == future


def test_cross_tenant_application_access_fails_closed(tmp_path: Path) -> None:
    (
        _database,
        _auth,
        access,
        service,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _fixture(tmp_path)
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)
    service.configure(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
        template_id=SCOPING_REVIEW,
        configuration={"secret": "tenant-a"},
    )
    service.configure(
        principal_b,
        workspace_id=workspace_b.id,
        project_id=project_b.id,
        template_id=INTEGRATIVE_REVIEW,
        configuration={"secret": "tenant-b"},
    )

    with pytest.raises(PermissionError):
        service.get(
            principal_b,
            workspace_id=workspace_a.id,
            project_id=project_a.id,
        )
    with pytest.raises(PermissionError):
        service.configure(
            principal_b,
            workspace_id=workspace_a.id,
            project_id=project_a.id,
            template_id=GENERIC_EVIDENCE_PROJECT,
        )


def test_viewer_can_read_application_but_cannot_manage_and_reviewer_gets_no_project_access(tmp_path: Path) -> None:
    database = tmp_path / "roles.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(
        email="app-owner@example.org",
        display_name="Owner",
        password="application owner password is sufficiently long",
    )
    viewer = auth.provision_user(
        email="app-viewer@example.org",
        display_name="Viewer",
        password="application viewer password is sufficiently long",
    )
    reviewer = auth.provision_user(
        email="app-reviewer@example.org",
        display_name="Reviewer",
        password="application reviewer password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(owner_user_id=owner.id, name="Lab", slug="app-lab")
    owner_principal = _principal(owner.id, access)
    project = access.create_project(owner_principal, workspace_id=workspace.id, name="Project", slug="project")
    access.add_or_update_member(
        owner_principal,
        workspace_id=workspace.id,
        user_id=viewer.id,
        role=WorkspaceRole.VIEWER,
    )
    access.add_or_update_member(
        owner_principal,
        workspace_id=workspace.id,
        user_id=reviewer.id,
        role=WorkspaceRole.REVIEWER,
    )
    service = ApplicationService(SQLiteApplicationStore(database), access)
    service.configure(
        owner_principal,
        workspace_id=workspace.id,
        project_id=project.id,
        template_id=GENERIC_EVIDENCE_PROJECT,
    )

    viewer_principal = _principal(viewer.id, access)
    assert service.get(viewer_principal, workspace_id=workspace.id, project_id=project.id) is not None
    with pytest.raises(PermissionError):
        service.configure(
            viewer_principal,
            workspace_id=workspace.id,
            project_id=project.id,
            template_id=SCOPING_REVIEW,
        )

    reviewer_principal = _principal(reviewer.id, access)
    with pytest.raises(PermissionError):
        service.get(reviewer_principal, workspace_id=workspace.id, project_id=project.id)

    assert Permission.APPLICATION_READ.value == "application.read"
    assert Permission.APPLICATION_MANAGE.value == "application.manage"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    cookie: str = "",
):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if cookie:
        headers["Cookie"] = cookie
    request = Request(url, data=data, headers=headers, method=method)
    try:
        response = urlopen(request, timeout=6)
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        return int(exc.code), json.loads(body) if body else {}, list(exc.headers.get_all("Set-Cookie") or [])
    body = response.read().decode("utf-8")
    return int(response.status), json.loads(body) if body else {}, list(response.headers.get_all("Set-Cookie") or [])


def _wait_for_server(base_url: str) -> None:
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        try:
            status, _body, _cookies = _http(base_url + "/api/health")
            if status == 200:
                return
        except (URLError, OSError, TimeoutError):
            pass
        time.sleep(0.1)
    raise AssertionError("secure_server did not become ready")


def _login(base_url: str, email: str, password: str) -> str:
    status, body, cookies = _http(
        base_url + "/api/auth/login",
        method="POST",
        payload={"email": email, "password": password},
    )
    assert status == 200, body
    parsed = SimpleCookie()
    parsed.load(cookies[0])
    return f"nutev_auth_session={parsed['nutev_auth_session'].value}"


def _select(base_url: str, cookie: str, workspace_id: str, project_id: str) -> None:
    status, body, _ = _http(
        base_url + "/api/context/select",
        method="POST",
        cookie=cookie,
        payload={"workspace_id": workspace_id, "project_id": project_id},
    )
    assert status == 200, body


@pytest.mark.integration_no_network
def test_http_application_context_ignores_foreign_project_id_from_body(tmp_path: Path) -> None:
    (
        database,
        _auth,
        _access,
        _service,
        _user_a,
        _user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _fixture(tmp_path)
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(
        {
            "NUTEV_AUTH_MODE": "pilot",
            "NUTEV_AUTH_DB": str(database),
            "NUTEV_AUTH_SESSION_TTL_SECONDS": "600",
            "NUTEV_ENVIRONMENT": "production",
            "NUTEV_DISABLE_NETWORK": "1",
        }
    )
    process = subprocess.Popen(
        [sys.executable, str(WEB / "secure_server.py"), "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server(base_url)
        cookie_a = _login(base_url, "app-a@example.org", "application a password is sufficiently long")
        cookie_b = _login(base_url, "app-b@example.org", "application b password is sufficiently long")
        _select(base_url, cookie_a, workspace_a.id, project_a.id)
        _select(base_url, cookie_b, workspace_b.id, project_b.id)

        status, templates, _ = _http(base_url + "/api/application/templates", cookie=cookie_a)
        assert status == 200, templates
        assert {item["template_id"] for item in templates["templates"]} == {
            GENERIC_EVIDENCE_PROJECT,
            SCOPING_REVIEW,
            INTEGRATIVE_REVIEW,
        }

        status, app_a, _ = _http(
            base_url + "/api/application",
            method="POST",
            cookie=cookie_a,
            payload={
                "template_id": SCOPING_REVIEW,
                "configuration": {"research_question": "A HTTP private question"},
            },
        )
        assert status == 201, app_a
        assert app_a["project_id"] == project_a.id

        status, app_b, _ = _http(
            base_url + "/api/application",
            method="POST",
            cookie=cookie_b,
            payload={
                "template_id": INTEGRATIVE_REVIEW,
                "project_id": project_a.id,
                "configuration": {"research_question": "B HTTP private question"},
            },
        )
        assert status == 201, app_b
        assert app_b["project_id"] == project_b.id
        assert app_b["application"]["project_id"] == project_b.id
        assert project_a.id not in json.dumps(app_b)

        status, read_a, _ = _http(base_url + "/api/application", cookie=cookie_a)
        assert status == 200, read_a
        assert "B HTTP private question" not in json.dumps(read_a)
        assert read_a["application"]["configuration"]["research_question"] == "A HTTP private question"

        status, read_b, _ = _http(base_url + "/api/application", cookie=cookie_b)
        assert status == 200, read_b
        assert "A HTTP private question" not in json.dumps(read_b)
        assert read_b["application"]["configuration"]["research_question"] == "B HTTP private question"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
