from __future__ import annotations

from http.cookies import SimpleCookie
import importlib.util
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
    Permission,
    PermissionService,
    Principal,
    ResearchContext,
    SQLiteAuthProvider,
    SQLiteSearchOwnershipStore,
    SQLiteWorkspaceProjectStore,
    SearchOwnershipError,
    SearchScopeService,
    WorkspaceProjectService,
    WorkspaceRole,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"
if str(WEB) not in sys.path:
    sys.path.insert(0, str(WEB))


def _load_search_adapter():
    spec = importlib.util.spec_from_file_location(
        "nutev_search_adapter_scope_test",
        WEB / "search_adapter.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


def _principal(user_id: str, access: WorkspaceProjectService) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(access.memberships_for_user(user_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )


def _platform(tmp_path: Path):
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user_a = auth.provision_user(
        email="a@example.org",
        display_name="Tenant A",
        password="tenant a password is sufficiently long",
    )
    user_b = auth.provision_user(
        email="b@example.org",
        display_name="Tenant B",
        password="tenant b password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace_a = access.provision_workspace(
        owner_user_id=user_a.id,
        name="Workspace A",
        slug="workspace-a",
    )
    workspace_b = access.provision_workspace(
        owner_user_id=user_b.id,
        name="Workspace B",
        slug="workspace-b",
    )
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
    scope = SearchScopeService(SQLiteSearchOwnershipStore(database), access)
    return (
        database,
        access,
        scope,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    )


def test_search_ownership_is_workspace_user_project_job_search(tmp_path: Path) -> None:
    (
        _database,
        access,
        scope,
        user_a,
        _user_b,
        workspace_a,
        _workspace_b,
        project_a,
        _project_b,
    ) = _platform(tmp_path)
    principal = _principal(user_a.id, access)
    job_id = "job_" + "a" * 32
    owner = scope.record_new_job(
        principal,
        ResearchContext(workspace_a.id, project_a.id),
        job_id=job_id,
    )
    assert owner.workspace_id == workspace_a.id
    assert owner.user_id == user_a.id
    assert owner.project_id == project_a.id
    assert owner.search_id is None

    search_id = "web_20260908T120000+0000_deadbeef"
    bound = scope.store.bind_search(job_id=job_id, search_id=search_id)
    assert bound.search_id == search_id
    assert scope.store.search_ids_for_workspace(workspace_a.id) == frozenset({search_id})
    assert scope.store.search_ids_for_project(workspace_a.id, project_a.id) == frozenset({search_id})


def test_search_ownership_conflicts_fail_closed(tmp_path: Path) -> None:
    (
        _database,
        access,
        scope,
        user_a,
        _user_b,
        workspace_a,
        _workspace_b,
        _project_a,
        _project_b,
    ) = _platform(tmp_path)
    principal = _principal(user_a.id, access)
    context = ResearchContext(workspace_a.id, None)
    job_id = "job_" + "b" * 32
    scope.record_new_job(principal, context, job_id=job_id)
    with pytest.raises(SearchOwnershipError):
        scope.record_new_job(principal, context, job_id=job_id)


def test_viewer_can_read_history_but_cannot_run_search(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(
        email="owner@example.org",
        display_name="Owner",
        password="owner password is sufficiently long",
    )
    viewer = auth.provision_user(
        email="viewer@example.org",
        display_name="Viewer",
        password="viewer password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(
        owner_user_id=owner.id,
        name="Lab",
        slug="lab",
    )
    owner_principal = _principal(owner.id, access)
    access.add_or_update_member(
        owner_principal,
        workspace_id=workspace.id,
        user_id=viewer.id,
        role=WorkspaceRole.VIEWER,
    )
    viewer_principal = _principal(viewer.id, access)
    context = access.authorization_context(viewer_principal, workspace_id=workspace.id)
    permissions = PermissionService()
    assert permissions.can(viewer_principal, Permission.SEARCH_HISTORY_READ, context=context)
    assert not permissions.can(viewer_principal, Permission.SEARCH_RUN, context=context)


def test_reviewer_cannot_read_entire_search_history(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(
        email="owner@example.org",
        display_name="Owner",
        password="owner password is sufficiently long",
    )
    reviewer = auth.provision_user(
        email="reviewer@example.org",
        display_name="Reviewer",
        password="reviewer password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace = access.provision_workspace(
        owner_user_id=owner.id,
        name="Lab",
        slug="lab",
    )
    owner_principal = _principal(owner.id, access)
    access.add_or_update_member(
        owner_principal,
        workspace_id=workspace.id,
        user_id=reviewer.id,
        role=WorkspaceRole.REVIEWER,
    )
    reviewer_principal = _principal(reviewer.id, access)
    scope = SearchScopeService(SQLiteSearchOwnershipStore(database), access)
    with pytest.raises(PermissionError):
        scope.authorized_search_ids(
            reviewer_principal,
            ResearchContext(workspace.id, None),
            scope="workspace",
        )


def test_exact_foreign_job_and_search_ids_remain_useless(tmp_path: Path) -> None:
    (
        _database,
        access,
        scope,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _platform(tmp_path)
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)
    job_id = "job_" + "c" * 32
    search_id = "web_20260908T120000+0000_cafebabe"
    scope.record_new_job(
        principal_a,
        ResearchContext(workspace_a.id, project_a.id),
        job_id=job_id,
    )
    scope.store.bind_search(job_id=job_id, search_id=search_id)

    with pytest.raises(PermissionError):
        scope.require_job_access(
            principal_b,
            ResearchContext(workspace_b.id, project_b.id),
            job_id,
        )
    with pytest.raises(PermissionError):
        scope.require_search_access(
            principal_b,
            ResearchContext(workspace_b.id, project_b.id),
            search_id,
        )


def test_workspace_switch_and_project_scope_filter_history(tmp_path: Path) -> None:
    database = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user = auth.provision_user(
        email="owner@example.org",
        display_name="Owner",
        password="owner password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    workspace_a = access.provision_workspace(
        owner_user_id=user.id,
        name="A",
        slug="a-workspace",
    )
    workspace_b = access.provision_workspace(
        owner_user_id=user.id,
        name="B",
        slug="b-workspace",
    )
    principal = _principal(user.id, access)
    project_a = access.create_project(
        principal,
        workspace_id=workspace_a.id,
        name="Project A",
        slug="project-a",
    )
    scope = SearchScopeService(SQLiteSearchOwnershipStore(database), access)

    workspace_job = "job_" + "d" * 32
    workspace_search = "web_20260908T120000+0000_aaaabbbb"
    scope.record_new_job(
        principal,
        ResearchContext(workspace_a.id, None),
        job_id=workspace_job,
    )
    scope.store.bind_search(job_id=workspace_job, search_id=workspace_search)

    project_job = "job_" + "e" * 32
    project_search = "web_20260908T120001+0000_ccccdddd"
    scope.record_new_job(
        principal,
        ResearchContext(workspace_a.id, project_a.id),
        job_id=project_job,
    )
    scope.store.bind_search(job_id=project_job, search_id=project_search)

    assert scope.authorized_search_ids(
        principal,
        ResearchContext(workspace_a.id, None),
        scope="workspace",
    ) == frozenset({workspace_search, project_search})
    assert scope.authorized_search_ids(
        principal,
        ResearchContext(workspace_a.id, project_a.id),
        scope="project",
    ) == frozenset({project_search})
    assert scope.authorized_search_ids(
        principal,
        ResearchContext(workspace_b.id, None),
        scope="workspace",
    ) == frozenset()
    with pytest.raises(PermissionError):
        scope.require_search_access(
            principal,
            ResearchContext(workspace_b.id, None),
            workspace_search,
        )


def test_persisted_search_readers_fail_closed_with_authorized_id_set(tmp_path: Path) -> None:
    adapter = _load_search_adapter()
    root = tmp_path / "output"
    allowed_id = "web_20260908T120000+0000_allowed1"
    legacy_id = "web_20260908T120001+0000_legacy01"
    for search_id, query in ((allowed_id, "allowed"), (legacy_id, "legacy unowned")):
        run_dir = root / "15_web_searches" / search_id
        run_dir.mkdir(parents=True)
        (run_dir / "result.json").write_text(
            json.dumps(
                {
                    "search_id": search_id,
                    "query": query,
                    "created_at": "2026-09-08T12:00:00+00:00",
                    "status": "COMPLETE",
                    "unique_records": 1,
                    "returned_records": 1,
                    "results": [],
                }
            ),
            encoding="utf-8",
        )

    allowed = frozenset({allowed_id})
    assert [
        item["search_id"]
        for item in adapter.list_search_runs(
            output_root=root,
            allowed_search_ids=allowed,
        )
    ] == [allowed_id]
    assert adapter.list_search_runs(
        output_root=root,
        allowed_search_ids=frozenset(),
    ) == []
    assert adapter.load_search_run(
        allowed_id,
        output_root=root,
        allowed_search_ids=allowed,
    )["query"] == "allowed"
    with pytest.raises(FileNotFoundError):
        adapter.load_search_run(
            legacy_id,
            output_root=root,
            allowed_search_ids=allowed,
        )


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
        return (
            int(exc.code),
            json.loads(body) if body else {},
            list(exc.headers.get_all("Set-Cookie") or []),
        )
    body = response.read().decode("utf-8")
    return (
        int(response.status),
        json.loads(body) if body else {},
        list(response.headers.get_all("Set-Cookie") or []),
    )


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


def _select(
    base_url: str,
    cookie: str,
    workspace_id: str,
    project_id: str | None,
) -> None:
    status, body, _ = _http(
        base_url + "/api/context/select",
        method="POST",
        cookie=cookie,
        payload={"workspace_id": workspace_id, "project_id": project_id},
    )
    assert status == 200, body


def _wait_job(base_url: str, cookie: str, job_id: str) -> dict[str, object]:
    deadline = time.monotonic() + 12
    last: dict[str, object] | None = None
    while time.monotonic() < deadline:
        status, body, _ = _http(
            base_url + f"/api/search/jobs/{job_id}",
            cookie=cookie,
        )
        assert status == 200, body
        last = body
        if body.get("status") in {"completed", "failed"}:
            return body
        time.sleep(0.1)
    raise AssertionError(f"job did not finish: {last}")


@pytest.mark.integration_no_network
def test_http_two_tenant_search_death_test(tmp_path: Path) -> None:
    (
        database,
        access,
        _scope,
        user_a,
        _user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _platform(tmp_path)
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
        [
            sys.executable,
            str(WEB / "secure_server.py"),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server(base_url)
        cookie_a = _login(
            base_url,
            "a@example.org",
            "tenant a password is sufficiently long",
        )
        cookie_b = _login(
            base_url,
            "b@example.org",
            "tenant b password is sufficiently long",
        )
        _select(base_url, cookie_a, workspace_a.id, project_a.id)
        _select(base_url, cookie_b, workspace_b.id, project_b.id)

        status, job, _ = _http(
            base_url + "/api/search/jobs",
            method="POST",
            cookie=cookie_a,
            payload={
                "query": "tenant scoped canary",
                "providers": ["pubmed"],
                "per_provider": 1,
                "max_results": 1,
            },
        )
        assert status == 202, job
        assert job["tenant_scope"] == {
            "workspace_id": workspace_a.id,
            "project_id": project_a.id,
        }
        job_id = str(job["job_id"])
        completed = _wait_job(base_url, cookie_a, job_id)
        assert completed["status"] == "completed"
        search_id = str(completed["search_id"])
        assert search_id.startswith("web_")

        status, body, _ = _http(
            base_url + f"/api/search/jobs/{job_id}",
            cookie=cookie_b,
        )
        assert status == 404
        assert body == {"error": "search_job_not_found"}

        status, body, _ = _http(
            base_url + f"/api/searches/{search_id}",
            cookie=cookie_b,
        )
        assert status == 404
        assert body == {"error": "search_not_found"}

        deadline = time.monotonic() + 8
        workspace_history = None
        while time.monotonic() < deadline:
            status, history, _ = _http(
                base_url + "/api/searches?limit=50&scope=workspace",
                cookie=cookie_a,
            )
            assert status == 200, history
            if any(
                item.get("search_id") == search_id
                for item in history.get("searches", [])
            ):
                workspace_history = history
                break
            time.sleep(0.1)
        assert workspace_history is not None

        status, project_history, _ = _http(
            base_url + "/api/searches?limit=50&scope=project",
            cookie=cookie_a,
        )
        assert status == 200, project_history
        assert search_id in {
            item.get("search_id") for item in project_history["searches"]
        }

        status, b_history, _ = _http(
            base_url + "/api/searches?limit=50&scope=workspace",
            cookie=cookie_b,
        )
        assert status == 200, b_history
        assert search_id not in {
            item.get("search_id") for item in b_history["searches"]
        }

        workspace_c = access.provision_workspace(
            owner_user_id=user_a.id,
            name="Workspace C",
            slug="workspace-c",
        )
        _select(base_url, cookie_a, workspace_c.id, None)
        status, switched_history, _ = _http(
            base_url + "/api/searches?limit=50&scope=workspace",
            cookie=cookie_a,
        )
        assert status == 200, switched_history
        assert search_id not in {
            item.get("search_id") for item in switched_history["searches"]
        }
        status, _body, _ = _http(
            base_url + f"/api/searches/{search_id}",
            cookie=cookie_a,
        )
        assert status == 404
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_search_history_ui_exposes_workspace_and_project_scopes_without_browser_storage() -> None:
    history = (WEB / "search-history-ui.js").read_text(encoding="utf-8")
    assert "Buscas do workspace" in history
    assert "Buscas do projeto" in history
    assert 'data-history-scope="workspace"' in history
    assert 'data-history-scope="project"' in history
    assert "localStorage" not in history
    assert "sessionStorage" not in history


def test_legacy_browser_session_path_remains_present_for_compatibility() -> None:
    server = (WEB / "secure_server.py").read_text(encoding="utf-8")
    assert (
        '"history_scope": "workspace_project" if mode == "pilot" else "browser_session"'
        in server
    )
    assert "_JOB_OWNERS[job_id] = owner_scope" in server
    assert "_start_job_owner_watch(job_id, owner_scope)" in server
    assert "filter_owned_runs(runs, owner_scope)" in server
    assert "search_owned_by(search_id, owner_scope)" in server
