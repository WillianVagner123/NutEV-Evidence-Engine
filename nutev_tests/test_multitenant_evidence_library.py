from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from argon2 import PasswordHasher
import pytest

from nutev.registry.migrations import apply_migrations
from nutev.tenancy import (
    EvidenceLibraryService,
    Permission,
    PermissionService,
    Principal,
    ResearchContext,
    SQLiteAuthProvider,
    SQLiteEvidenceLibraryStore,
    SQLiteWorkspaceProjectStore,
    GlobalEvidenceRegistryReader,
    WorkspaceProjectService,
    WorkspaceRole,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


def _registry_with_article(tmp_path: Path) -> tuple[Path, str]:
    database = tmp_path / "registry" / "article_registry.sqlite"
    database.parent.mkdir(parents=True)
    article_id = "art_global_shared_001"
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(database) as connection:
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
                "Shared Global Evidence Document",
                2026,
                "Journal of Shared Evidence",
                "Public bibliographic abstract.",
                now,
                now,
                now,
                now,
            ),
        )
        for scheme, value in (
            ("doi", "10.1000/shared.001"),
            ("pmid", "12345678"),
        ):
            connection.execute(
                """
                INSERT INTO article_aliases(
                    article_id, scheme, normalized_value, raw_value, provider,
                    first_seen_at, last_seen_at
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (article_id, scheme, value, value, "fixture", now, now),
            )
        connection.commit()
    return database, article_id


def _principal(user_id: str, access: WorkspaceProjectService) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(access.memberships_for_user(user_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )


def _platform(tmp_path: Path):
    platform = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(platform, password_hasher=_fast_hasher())
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
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(platform))
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
    return (
        platform,
        auth,
        access,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    )


def _library(tmp_path: Path):
    registry_db, article_id = _registry_with_article(tmp_path)
    (
        platform,
        _auth,
        access,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _platform(tmp_path)
    service = EvidenceLibraryService(
        SQLiteEvidenceLibraryStore(platform),
        GlobalEvidenceRegistryReader(registry_db),
        access,
    )
    return (
        platform,
        registry_db,
        article_id,
        access,
        service,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    )


def test_same_global_document_has_independent_private_placements(tmp_path: Path) -> None:
    (
        _platform,
        _registry_db,
        article_id,
        access,
        service,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _library(tmp_path)
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)

    entry_a = service.save(
        principal_a,
        ResearchContext(workspace_a.id, project_a.id),
        article_id=article_id,
        scope="project",
        state="included",
        tags=["A-tag"],
        notes="private note from A",
    )
    entry_b = service.save(
        principal_b,
        ResearchContext(workspace_b.id, project_b.id),
        article_id=article_id,
        scope="project",
        state="background",
        tags=["B-tag"],
        notes="private note from B",
    )

    assert entry_a.document.article_id == entry_b.document.article_id == article_id
    assert entry_a.document.title == entry_b.document.title
    assert entry_a.placement.placement_id != entry_b.placement.placement_id
    assert entry_a.placement.state == "included"
    assert entry_b.placement.state == "background"
    assert entry_a.placement.notes == "private note from A"
    assert entry_b.placement.notes == "private note from B"
    assert not hasattr(entry_a.document, "state")
    assert not hasattr(entry_a.document, "notes")


def test_update_or_delete_in_tenant_a_never_mutates_tenant_b_or_global_document(tmp_path: Path) -> None:
    (
        _platform,
        _registry_db,
        article_id,
        access,
        service,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _library(tmp_path)
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)
    context_a = ResearchContext(workspace_a.id, project_a.id)
    context_b = ResearchContext(workspace_b.id, project_b.id)

    a = service.save(
        principal_a,
        context_a,
        article_id=article_id,
        scope="project",
        state="not_screened",
        notes="A v1",
    )
    b = service.save(
        principal_b,
        context_b,
        article_id=article_id,
        scope="project",
        state="background",
        notes="B stable",
    )
    updated_a = service.save(
        principal_a,
        context_a,
        article_id=article_id,
        scope="project",
        state="included",
        tags=["updated"],
        notes="A v2",
    )
    assert updated_a.placement.placement_id == a.placement.placement_id
    assert updated_a.placement.notes == "A v2"
    assert service.require_placement(principal_b, context_b, b.placement.placement_id).placement.notes == "B stable"

    assert service.delete(principal_a, context_a, a.placement.placement_id)
    with pytest.raises(KeyError):
        service.require_placement(principal_a, context_a, a.placement.placement_id)
    assert service.require_placement(principal_b, context_b, b.placement.placement_id).document.article_id == article_id
    assert service.registry.get(article_id) is not None


def test_exact_foreign_placement_id_does_not_cross_tenant_boundary(tmp_path: Path) -> None:
    (
        _platform,
        _registry_db,
        article_id,
        access,
        service,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _library(tmp_path)
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)
    entry_a = service.save(
        principal_a,
        ResearchContext(workspace_a.id, project_a.id),
        article_id=article_id,
        scope="project",
        notes="A secret placement",
    )
    with pytest.raises(KeyError):
        service.require_placement(
            principal_b,
            ResearchContext(workspace_b.id, project_b.id),
            entry_a.placement.placement_id,
        )


def test_workspace_and_project_placements_are_distinct_relations(tmp_path: Path) -> None:
    (
        _platform,
        _registry_db,
        article_id,
        access,
        service,
        user_a,
        _user_b,
        workspace_a,
        _workspace_b,
        project_a,
        _project_b,
    ) = _library(tmp_path)
    principal = _principal(user_a.id, access)
    context = ResearchContext(workspace_a.id, project_a.id)
    workspace_entry = service.save(
        principal,
        context,
        article_id=article_id,
        scope="workspace",
        notes="workspace note",
    )
    project_entry = service.save(
        principal,
        context,
        article_id=article_id,
        scope="project",
        notes="project note",
    )
    assert workspace_entry.placement.placement_id != project_entry.placement.placement_id
    assert workspace_entry.placement.project_id is None
    assert project_entry.placement.project_id == project_a.id
    project_entries = service.list(principal, context, scope="project")
    assert [item.placement.placement_id for item in project_entries] == [project_entry.placement.placement_id]
    workspace_entries = service.list(principal, context, scope="workspace")
    assert {item.placement.placement_id for item in workspace_entries} == {
        workspace_entry.placement.placement_id,
        project_entry.placement.placement_id,
    }


def test_viewer_reads_library_but_cannot_write_and_reviewer_cannot_list_all(tmp_path: Path) -> None:
    registry_db, article_id = _registry_with_article(tmp_path)
    platform = tmp_path / "platform.sqlite3"
    auth = SQLiteAuthProvider(platform, password_hasher=_fast_hasher())
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
    reviewer = auth.provision_user(
        email="reviewer@example.org",
        display_name="Reviewer",
        password="reviewer password is sufficiently long",
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(platform))
    workspace = access.provision_workspace(owner_user_id=owner.id, name="Lab", slug="lab")
    owner_principal = _principal(owner.id, access)
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
    service = EvidenceLibraryService(
        SQLiteEvidenceLibraryStore(platform),
        GlobalEvidenceRegistryReader(registry_db),
        access,
    )
    context = ResearchContext(workspace.id, None)
    service.save(owner_principal, context, article_id=article_id, notes="owner note")

    viewer_principal = _principal(viewer.id, access)
    assert len(service.list(viewer_principal, context)) == 1
    with pytest.raises(PermissionError):
        service.save(viewer_principal, context, article_id=article_id, notes="viewer write")

    reviewer_principal = _principal(reviewer.id, access)
    with pytest.raises(PermissionError):
        service.list(reviewer_principal, context)


def test_full_text_access_grant_is_private_expiring_and_cache_path_is_not_public(tmp_path: Path) -> None:
    (
        _platform,
        _registry_db,
        article_id,
        access,
        service,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _library(tmp_path)
    principal_a = _principal(user_a.id, access)
    principal_b = _principal(user_b.id, access)
    context_a = ResearchContext(workspace_a.id, project_a.id)
    context_b = ResearchContext(workspace_b.id, project_b.id)

    active = service.create_full_text_grant(
        principal_a,
        context_a,
        article_id=article_id,
        scope="project",
        artifact_id="fta_shared_hash",
        provider_record_id="provider-record-a",
        access_type="subscription",
        license_text="institutional",
        access_url="https://example.org/fulltext/a",
        cache_path="/private/workspace-a/article.pdf",
        redistribution_allowed=False,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    service.create_full_text_grant(
        principal_a,
        context_a,
        article_id=article_id,
        scope="project",
        access_type="temporary",
        cache_path="/private/expired.pdf",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    grants_a = service.full_text_access(principal_a, context_a, article_id)
    assert [grant.grant_id for grant in grants_a] == [active.grant_id]
    descriptor = grants_a[0].public_descriptor()
    assert "cache_path" not in descriptor
    assert "storage_path" not in descriptor
    assert descriptor["redistribution_allowed"] is False
    assert service.full_text_access(principal_b, context_b, article_id) == ()


def test_global_registry_reader_never_exposes_full_text_storage_fields(tmp_path: Path) -> None:
    registry_db, article_id = _registry_with_article(tmp_path)
    document = GlobalEvidenceRegistryReader(registry_db).get(article_id)
    assert document is not None
    serialized = json.dumps(
        {
            "article_id": document.article_id,
            "title": document.title,
            "abstract": document.abstract,
            "doi": document.doi,
        }
    )
    assert "storage_path" not in serialized
    assert "cache_path" not in serialized
    assert "full_text" not in serialized


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
def test_http_same_global_article_private_placement_death_test(tmp_path: Path) -> None:
    registry_db, article_id = _registry_with_article(tmp_path)
    (
        platform,
        _auth,
        access,
        user_a,
        user_b,
        workspace_a,
        workspace_b,
        project_a,
        project_b,
    ) = _platform(tmp_path)
    service = EvidenceLibraryService(
        SQLiteEvidenceLibraryStore(platform),
        GlobalEvidenceRegistryReader(registry_db),
        access,
    )
    service.create_full_text_grant(
        _principal(user_a.id, access),
        ResearchContext(workspace_a.id, project_a.id),
        article_id=article_id,
        scope="project",
        access_type="subscription",
        access_url="https://example.org/a",
        cache_path="/never/expose/workspace-a.pdf",
        redistribution_allowed=False,
    )

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(
        {
            "NUTEV_AUTH_MODE": "pilot",
            "NUTEV_AUTH_DB": str(platform),
            "NUTEV_REGISTRY_DB": str(registry_db),
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

        status, a_saved, _ = _http(
            base_url + "/api/library/placements",
            method="POST",
            cookie=cookie_a,
            payload={
                "article_id": article_id,
                "scope": "project",
                "state": "included",
                "tags": ["tenant-a"],
                "notes": "A private HTTP note",
            },
        )
        assert status == 201, a_saved
        placement_a = a_saved["placement"]["placement_id"]

        status, body, _ = _http(
            base_url + f"/api/library/placements/{placement_a}",
            cookie=cookie_b,
        )
        assert status == 404
        assert body == {"error": "placement_not_found"}

        status, b_saved, _ = _http(
            base_url + "/api/library/placements",
            method="POST",
            cookie=cookie_b,
            payload={
                "article_id": article_id,
                "scope": "project",
                "state": "background",
                "tags": ["tenant-b"],
                "notes": "B private HTTP note",
            },
        )
        assert status == 201, b_saved
        placement_b = b_saved["placement"]["placement_id"]
        assert placement_a != placement_b
        assert a_saved["document"]["article_id"] == b_saved["document"]["article_id"] == article_id

        status, a_library, _ = _http(
            base_url + "/api/library?scope=project",
            cookie=cookie_a,
        )
        assert status == 200, a_library
        assert [item["placement"]["placement_id"] for item in a_library["entries"]] == [placement_a]
        assert "B private HTTP note" not in json.dumps(a_library)

        status, b_library, _ = _http(
            base_url + "/api/library?scope=project",
            cookie=cookie_b,
        )
        assert status == 200, b_library
        assert [item["placement"]["placement_id"] for item in b_library["entries"]] == [placement_b]
        assert "A private HTTP note" not in json.dumps(b_library)

        status, access_payload, _ = _http(
            base_url + f"/api/library/full-text/{article_id}",
            cookie=cookie_a,
        )
        assert status == 200, access_payload
        encoded = json.dumps(access_payload)
        assert "/never/expose/workspace-a.pdf" not in encoded
        assert "cache_path" not in encoded
        assert "storage_path" not in encoded
        assert len(access_payload["grants"]) == 1

        status, b_access, _ = _http(
            base_url + f"/api/library/full-text/{article_id}",
            cookie=cookie_b,
        )
        assert status == 200, b_access
        assert b_access["grants"] == []

        status, deleted, _ = _http(
            base_url + f"/api/library/placements/{placement_a}",
            method="DELETE",
            cookie=cookie_a,
        )
        assert status == 200, deleted
        assert deleted["deleted"] is True

        status, b_after, _ = _http(
            base_url + f"/api/library/placements/{placement_b}",
            cookie=cookie_b,
        )
        assert status == 200, b_after
        assert b_after["placement"]["notes"] == "B private HTTP note"
        assert GlobalEvidenceRegistryReader(registry_db).get(article_id) is not None
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_library_permissions_are_explicit() -> None:
    source = PermissionService()
    assert source is not None
    assert Permission.EVIDENCE_LIBRARY_READ.value == "evidence_library.read"
    assert Permission.EVIDENCE_LIBRARY_WRITE.value == "evidence_library.write"
    assert Permission.FULL_TEXT_ACCESS_READ.value == "full_text_access.read"
    assert Permission.FULL_TEXT_ACCESS_MANAGE.value == "full_text_access.manage"
