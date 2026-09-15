from __future__ import annotations

from http.cookies import SimpleCookie
import json
from pathlib import Path
import sqlite3
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

import pytest

from nutev.tenancy import SQLiteAuthProvider
from nutev.tenancy.access_requests import SQLiteAccessRequestStore
from tools.pilot_closeout_fixture import pilot_server


def _http(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    cookie: str = "",
) -> tuple[int, dict[str, object], list[str]]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if cookie:
        headers["Cookie"] = cookie
    request = Request(url, data=data, headers=headers, method=method)
    try:
        response = urlopen(request, timeout=8)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        body = json.loads(raw) if raw else {}
        return int(exc.code), body, list(exc.headers.get_all("Set-Cookie") or [])
    raw = response.read().decode("utf-8")
    body = json.loads(raw) if raw else {}
    return int(response.status), body, list(response.headers.get_all("Set-Cookie") or [])


def _auth_cookie(headers: list[str]) -> str:
    for header in headers:
        parsed = SimpleCookie()
        parsed.load(header)
        morsel = parsed.get("nutev_auth_session")
        if morsel:
            return f"nutev_auth_session={morsel.value}"
    raise AssertionError("authentication cookie missing")


def test_access_store_token_is_hash_only_and_rejection_revokes_invitation(tmp_path: Path) -> None:
    database = tmp_path / "access.sqlite3"
    store = SQLiteAccessRequestStore(database)
    request = store.submit(
        email="new.researcher@example.org",
        display_name="New Researcher",
        institution="Example University",
        intended_use="Systematic review methods and evidence organization.",
    )
    assert request is not None
    invitation = store.approve(request.id, decided_by="usr_" + "a" * 32)
    assert store.inspect_invitation(invitation.token) is not None

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT invitation_token_hash FROM platform_access_requests WHERE id = ?",
            (request.id,),
        ).fetchone()
    assert row is not None
    persisted = str(row[0])
    assert invitation.token not in persisted
    assert len(persisted) == 64

    rejected = store.reject(request.id, decided_by="usr_" + "a" * 32, reason="Not in current pilot scope")
    assert rejected.status == "rejected"
    assert store.inspect_invitation(invitation.token) is None


def test_existing_account_or_open_request_is_not_duplicated(tmp_path: Path) -> None:
    database = tmp_path / "dedupe.sqlite3"
    provider = SQLiteAuthProvider(database)
    provider.provision_user(
        email="existing@example.org",
        display_name="Existing User",
        password="a sufficiently long existing password",
    )
    store = SQLiteAccessRequestStore(database)
    assert store.submit(
        email="existing@example.org",
        display_name="Existing User",
        institution="Example University",
        intended_use="Attempt to request an account that already exists.",
    ) is None

    first = store.submit(
        email="pending@example.org",
        display_name="Pending User",
        institution="Example University",
        intended_use="Research evidence organization for an academic project.",
    )
    assert first is not None
    second = store.submit(
        email="PENDING@example.org",
        display_name="Pending User",
        institution="Example University",
        intended_use="Duplicate request should not create another open record.",
    )
    assert second is None
    assert len(store.list(status="pending")) == 1


@pytest.mark.integration_no_network
def test_public_request_admin_approval_password_creation_and_first_login() -> None:
    with pilot_server() as (base, data, _root):
        email = "approved.researcher@example.org"
        request_payload = {
            "display_name": "Approved Researcher",
            "email": email,
            "institution": "Example University",
            "intended_use": "Evidence synthesis and governed literature review for a research project.",
            "website": "",
        }

        status, body, _cookies = _http(
            base + "/api/access-requests",
            method="POST",
            payload=request_payload,
        )
        assert status == 202
        assert body["status"] == "received"

        # Duplicate submissions remain deliberately indistinguishable to the caller.
        status, body, _cookies = _http(
            base + "/api/access-requests",
            method="POST",
            payload=request_payload,
        )
        assert status == 202
        assert body["status"] == "received"

        status, body, _cookies = _http(base + "/api/admin/access-requests?status=pending")
        assert status == 401
        assert body["error"] == "authentication_required"

        admin = data["users"]["admin"]
        status, body, cookies = _http(
            base + "/api/auth/login",
            method="POST",
            payload={"email": admin["email"], "password": admin["password"]},
        )
        assert status == 200
        assert "PLATFORM_ADMIN" in body["global_roles"]
        admin_cookie = _auth_cookie(cookies)

        status, body, _cookies = _http(
            base + "/api/admin/access-requests?status=pending",
            cookie=admin_cookie,
        )
        assert status == 200
        requests = [item for item in body["requests"] if item["email"] == email]
        assert len(requests) == 1
        request_id = str(requests[0]["id"])

        status, body, _cookies = _http(
            base + f"/api/admin/access-requests/{request_id}/approve",
            method="POST",
            payload={},
            cookie=admin_cookie,
        )
        assert status == 200
        assert body["status"] == "approved"
        invitation_path = str(body["invitation_path"])
        token = parse_qs(urlparse(invitation_path).query)["token"][0]
        assert len(token) >= 32

        with sqlite3.connect(data["database"]) as connection:
            row = connection.execute(
                "SELECT invitation_token_hash FROM platform_access_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        assert row is not None
        assert token not in str(row[0])
        assert len(str(row[0])) == 64

        status, body, _cookies = _http(
            base + "/api/access-invitations/status?token=" + token,
        )
        assert status == 200
        assert body["valid"] is True
        assert body["email"] == email

        password = "new approved researcher password 456"
        status, body, _cookies = _http(
            base + "/api/access-invitations/accept",
            method="POST",
            payload={"token": token, "password": password},
        )
        assert status == 201
        assert body["status"] == "account_created"
        assert body["email"] == email

        status, body, _cookies = _http(
            base + "/api/access-invitations/status?token=" + token,
        )
        assert status == 200
        assert body["valid"] is False

        status, body, cookies = _http(
            base + "/api/auth/login",
            method="POST",
            payload={"email": email, "password": password},
        )
        assert status == 200
        user_cookie = _auth_cookie(cookies)
        assert body["global_roles"] == []
        assert body["workspace_memberships"] == []

        # Account creation does not silently grant a workspace/project.
        status, context, _cookies = _http(base + "/api/context", cookie=user_cookie)
        assert status == 200
        assert context["current"]["workspace_id"] is None
        assert context["current"]["project_id"] is None

        # A normal newly-created user cannot read the administration queue.
        status, body, _cookies = _http(
            base + "/api/admin/access-requests?status=all",
            cookie=user_cookie,
        )
        assert status == 403
        assert body["error"] == "platform_admin_required"


def test_access_pages_expose_request_and_admin_entrypoints() -> None:
    root = Path(__file__).resolve().parents[1]
    web = root / "apps" / "nutev-web"
    login = (web / "login.html").read_text(encoding="utf-8")
    request_page = (web / "access-request.html").read_text(encoding="utf-8")
    password_page = (web / "set-password.html").read_text(encoding="utf-8")
    admin_page = (web / "access-admin.html").read_text(encoding="utf-8")
    boundary = (web / "request_boundary.py").read_text(encoding="utf-8")

    assert 'href="/access-request.html"' in login
    assert 'href="/access-admin.html"' in login
    assert "/api/access-requests" in request_page or "access-request.js" in request_page
    assert "set-password.js" in password_page
    assert "access-admin.js" in admin_page
    assert '"/api/access-invitations"' in boundary
    assert '"/api/admin/access-requests"' in boundary
