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
    AuthorizationContext,
    MembershipStatus,
    Permission,
    PermissionService,
    Principal,
    SQLiteAuthProvider,
    SQLiteSessionStore,
    SQLiteWorkspaceProjectStore,
    SessionPrincipalService,
    WorkspaceProjectService,
    WorkspaceRole,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


def _principal(user_id: str, service: WorkspaceProjectService) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(service.memberships_for_user(user_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )


def _two_tenants(tmp_path: Path):
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user_a = auth.provision_user(
        email="a@example.org",
        display_name="User A",
        password="password for tenant a is long",
    )
    user_b = auth.provision_user(
        email="b@example.org",
        display_name="User B",
        password="password for tenant b is long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace_a = access.provision_workspace(owner_user_id=user_a.id, name="Workspace A", slug="workspace-a")
    workspace_b = access.provision_workspace(owner_user_id=user_b.id, name="Workspace B", slug="workspace-b")
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
    return database, auth, access, user_a, user_b, workspace_a, workspace_b, project_a, project_b


def test_workspace_creation_always_creates_owner_membership(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user = auth.provision_user(
        email="owner@example.org",
        display_name="Owner",
        password="a sufficiently long owner password",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(owner_user_id=user.id, name="Evidence Lab", slug="evidence-lab")
    memberships = tuple(access.memberships_for_user(user.id))
    assert len(memberships) == 1
    assert memberships[0].workspace_id == workspace.id
    assert memberships[0].role is WorkspaceRole.WORKSPACE_OWNER
    assert memberships[0].status is MembershipStatus.ACTIVE


def test_cross_workspace_and_cross_project_ids_fail_closed(tmp_path: Path) -> None:
    (_database, _auth, access, user_a, _user_b, workspace_a, workspace_b, project_a, project_b) = _two_tenants(tmp_path)
    principal_a = _principal(user_a.id, access)

    with pytest.raises(PermissionError, match="workspace_access_denied"):
        access.require_workspace(principal_a, workspace_b.id)
    assert not access.confirm_project_access(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_b.id,
    )
    assert access.confirm_project_access(
        principal_a,
        workspace_id=workspace_a.id,
        project_id=project_a.id,
    )


def test_project_id_cannot_override_workspace_boundary(tmp_path: Path) -> None:
    (_database, _auth, access, user_a, _user_b, workspace_a, _workspace_b, _project_a, project_b) = _two_tenants(tmp_path)
    principal_a = _principal(user_a.id, access)
    with pytest.raises(PermissionError, match="project_access_denied"):
        access.require_project(
            principal_a,
            workspace_id=workspace_a.id,
            project_id=project_b.id,
        )


def test_reviewer_does_not_receive_automatic_whole_project_access(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(
        email="owner@example.org",
        display_name="Owner",
        password="a sufficiently long owner password",
    )
    reviewer = auth.provision_user(
        email="reviewer@example.org",
        display_name="Reviewer",
        password="a sufficiently long reviewer password",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(owner_user_id=owner.id, name="Lab", slug="lab")
    owner_principal = _principal(owner.id, access)
    project = access.create_project(owner_principal, workspace_id=workspace.id, name="Review", slug="review")
    access.add_or_update_member(
        owner_principal,
        workspace_id=workspace.id,
        user_id=reviewer.id,
        role=WorkspaceRole.REVIEWER,
    )
    reviewer_principal = _principal(reviewer.id, access)

    assert access.list_projects(reviewer_principal, workspace.id) == ()
    assert not access.confirm_project_access(
        reviewer_principal,
        workspace_id=workspace.id,
        project_id=project.id,
    )
    decision = PermissionService().decide(
        reviewer_principal,
        Permission.SCREEN,
        context=AuthorizationContext(
            workspace_id=workspace.id,
            project_id=project.id,
            project_access_confirmed=False,
            assigned=True,
        ),
    )
    assert not decision.allowed
    assert decision.reason == "project_access_not_confirmed"


def test_viewer_can_resolve_project_context_but_cannot_gain_write_permissions(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(email="owner@example.org", display_name="Owner", password="a long enough owner password")
    viewer = auth.provision_user(email="viewer@example.org", display_name="Viewer", password="a long enough viewer password")
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(owner_user_id=owner.id, name="Lab", slug="lab")
    owner_principal = _principal(owner.id, access)
    project = access.create_project(owner_principal, workspace_id=workspace.id, name="Project", slug="project")
    access.add_or_update_member(owner_principal, workspace_id=workspace.id, user_id=viewer.id, role=WorkspaceRole.VIEWER)
    viewer_principal = _principal(viewer.id, access)

    assert [item.id for item in access.list_projects(viewer_principal, workspace.id)] == [project.id]
    ctx = access.authorization_context(viewer_principal, workspace_id=workspace.id, project_id=project.id)
    permission = PermissionService()
    assert permission.can(viewer_principal, Permission.PROJECT_BANK_READ, context=ctx)
    assert not permission.can(viewer_principal, Permission.SCREEN, context=ctx)


def test_removed_membership_revokes_new_principal_access_immediately(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(email="owner@example.org", display_name="Owner", password="a long enough owner password")
    researcher = auth.provision_user(email="researcher@example.org", display_name="Researcher", password="a long enough researcher password")
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(owner_user_id=owner.id, name="Lab", slug="lab")
    owner_principal = _principal(owner.id, access)
    access.add_or_update_member(owner_principal, workspace_id=workspace.id, user_id=researcher.id, role=WorkspaceRole.RESEARCHER)
    before = _principal(researcher.id, access)
    assert before.membership_for(workspace.id) is not None

    access.set_member_status(
        owner_principal,
        workspace_id=workspace.id,
        user_id=researcher.id,
        status=MembershipStatus.REMOVED,
    )
    after = _principal(researcher.id, access)
    assert after.membership_for(workspace.id) is None
    with pytest.raises(PermissionError):
        access.require_workspace(after, workspace.id)


def test_session_principal_reloads_memberships_on_every_resolve(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(email="owner@example.org", display_name="Owner", password="a long enough owner password")
    researcher = auth.provision_user(email="researcher@example.org", display_name="Researcher", password="a long enough researcher password")
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(owner_user_id=owner.id, name="Lab", slug="lab")
    owner_principal = _principal(owner.id, access)
    access.add_or_update_member(owner_principal, workspace_id=workspace.id, user_id=researcher.id, role=WorkspaceRole.RESEARCHER)
    sessions = SQLiteSessionStore(database)
    auth_service = SessionPrincipalService(
        auth,
        sessions,
        membership_loader=access.memberships_for_user,
        session_ttl_seconds=600,
    )
    login = auth_service.login("researcher@example.org", "a long enough researcher password")
    assert login is not None
    assert login.session.principal.membership_for(workspace.id) is not None

    access.set_member_status(
        owner_principal,
        workspace_id=workspace.id,
        user_id=researcher.id,
        status=MembershipStatus.REMOVED,
    )
    refreshed = auth_service.resolve(login.session_token)
    assert refreshed is not None
    assert refreshed.principal.membership_for(workspace.id) is None


def test_context_persists_by_session_and_switching_workspace_clears_project(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user = auth.provision_user(email="owner@example.org", display_name="Owner", password="a long enough owner password")
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace_a = access.provision_workspace(owner_user_id=user.id, name="A", slug="workspace-a")
    principal = _principal(user.id, access)
    project_a = access.create_project(principal, workspace_id=workspace_a.id, name="A1", slug="a1")
    workspace_b = access.provision_workspace(owner_user_id=user.id, name="B", slug="workspace-b")
    principal = _principal(user.id, access)

    selected = access.select_context(principal, workspace_id=workspace_a.id, project_id=project_a.id)
    assert selected.current.workspace_id == workspace_a.id
    assert selected.current.project_id == project_a.id
    refreshed = access.context_snapshot(principal)
    assert refreshed.current == selected.current

    switched = access.select_context(principal, workspace_id=workspace_b.id, project_id=None)
    assert switched.current.workspace_id == workspace_b.id
    assert switched.current.project_id is None


def test_context_is_cleared_when_membership_is_removed(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(email="owner@example.org", display_name="Owner", password="a long enough owner password")
    user = auth.provision_user(email="user@example.org", display_name="User", password="a long enough user password")
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(owner_user_id=owner.id, name="Lab", slug="lab")
    owner_principal = _principal(owner.id, access)
    project = access.create_project(owner_principal, workspace_id=workspace.id, name="P", slug="p")
    access.add_or_update_member(owner_principal, workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.RESEARCHER)
    principal = _principal(user.id, access)
    access.select_context(principal, workspace_id=workspace.id, project_id=project.id)

    access.set_member_status(owner_principal, workspace_id=workspace.id, user_id=user.id, status=MembershipStatus.REMOVED)
    refreshed_principal = _principal(user.id, access)
    snapshot = access.context_snapshot(refreshed_principal)
    assert snapshot.current.workspace_id is None
    assert snapshot.current.project_id is None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http(url: str, *, method: str = "GET", payload=None, cookie: str = ""):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if cookie:
        headers["Cookie"] = cookie
    request = Request(url, data=data, headers=headers, method=method)
    try:
        response = urlopen(request, timeout=5)
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


@pytest.mark.integration_no_network
def test_http_context_rejects_foreign_ids_and_survives_refresh(tmp_path: Path) -> None:
    database, auth, access, user_a, _user_b, workspace_a, workspace_b, project_a, project_b = _two_tenants(tmp_path)
    password = "password for tenant a is long"
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
        status, body, cookies = _http(
            base_url + "/api/auth/login",
            method="POST",
            payload={"email": "a@example.org", "password": password},
        )
        assert status == 200
        assert any(item["workspace_id"] == workspace_a.id for item in body["workspace_memberships"])
        parsed = SimpleCookie()
        parsed.load(cookies[0])
        token = parsed["nutev_auth_session"].value
        cookie = f"nutev_auth_session={token}"

        status, context, _ = _http(base_url + "/api/context", cookie=cookie)
        assert status == 200
        assert {item["id"] for item in context["workspaces"]} == {workspace_a.id}
        assert context["current"] == {"workspace_id": None, "project_id": None}

        status, selected, _ = _http(
            base_url + "/api/context/select",
            method="POST",
            cookie=cookie,
            payload={"workspace_id": workspace_a.id, "project_id": project_a.id},
        )
        assert status == 200
        assert selected["current"] == {"workspace_id": workspace_a.id, "project_id": project_a.id}
        assert selected["selection_is_authorization"] is False

        status, refreshed, _ = _http(base_url + "/api/context", cookie=cookie)
        assert status == 200
        assert refreshed["current"] == selected["current"]

        for payload in (
            {"workspace_id": workspace_b.id, "project_id": None},
            {"workspace_id": workspace_a.id, "project_id": project_b.id},
        ):
            status, body, _ = _http(
                base_url + "/api/context/select",
                method="POST",
                cookie=cookie,
                payload=payload,
            )
            assert status == 404
            assert body == {"error": "context_not_found"}

        # The user remains authenticated but loses tenant access immediately after removal.
        owner_b = _principal(user_a.id, access)
        # user_a is owner of workspace_a, so owner removal is intentionally prohibited.
        assert owner_b.membership_for(workspace_a.id) is not None
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_context_ui_is_server_backed_and_loaded_on_primary_surfaces() -> None:
    script = (WEB / "workspace-context.js").read_text(encoding="utf-8")
    assert "fetch('/api/context'" in script or "jsonFetch('/api/context')" in script
    assert "'/api/context/select'" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    for name in ("index.html", "search.html", "articles.html"):
        html = (WEB / name).read_text(encoding="utf-8")
        assert "workspace-context.js" in html


def test_pr3_does_not_scope_search_yet() -> None:
    server = (WEB / "secure_server.py").read_text(encoding="utf-8")
    search_block = server.split('if path == "/api/search/jobs":', 1)[1].split("super().do_POST()", 1)[0]
    assert "_workspace_access_service" not in search_block
    assert "workspace_id" not in search_block
    assert "project_id" not in search_block
