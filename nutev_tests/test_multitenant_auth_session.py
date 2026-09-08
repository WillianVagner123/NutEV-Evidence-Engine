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

from nutev.tenancy import (
    GlobalRole,
    SQLiteAuthProvider,
    SQLiteSessionStore,
    SessionPrincipalService,
)

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


def _provider(tmp_path: Path) -> tuple[SQLiteAuthProvider, Path]:
    database = tmp_path / "auth.sqlite3"
    return SQLiteAuthProvider(database, password_hasher=_fast_hasher()), database


def _provision(provider: SQLiteAuthProvider, *, password: str = "correct horse battery staple"):
    return provider.provision_user(
        email="researcher@example.org",
        display_name="Researcher",
        password=password,
    )


def test_password_is_argon2_hashed_and_bad_credentials_fail(tmp_path: Path) -> None:
    provider, database = _provider(tmp_path)
    password = "correct horse battery staple"
    user = _provision(provider, password=password)

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT password_hash FROM platform_auth_users WHERE id = ?",
            (user.id,),
        ).fetchone()
    assert row is not None
    stored = str(row[0])
    assert stored.startswith("$argon2")
    assert password not in stored

    assert provider.authenticate("researcher@example.org", "wrong password value") is None
    authenticated = provider.authenticate("RESEARCHER@example.org", password)
    assert authenticated is not None
    assert authenticated.user.id == user.id


def test_short_password_is_rejected_at_provisioning(tmp_path: Path) -> None:
    provider, _database = _provider(tmp_path)
    with pytest.raises(ValueError, match="at least"):
        provider.provision_user(
            email="researcher@example.org",
            display_name="Researcher",
            password="short",
        )


def test_session_store_persists_only_token_hash(tmp_path: Path) -> None:
    provider, database = _provider(tmp_path)
    user = _provision(provider)
    store = SQLiteSessionStore(database)
    issued = store.issue(user.id, ttl_seconds=600)

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT token_hash FROM platform_auth_sessions WHERE session_id = ?",
            (issued.session_id,),
        ).fetchone()
    assert row is not None
    persisted = str(row[0])
    assert persisted != issued.session_token
    assert issued.session_token not in persisted
    assert len(persisted) == 64
    assert store.resolve(issued.session_token) is not None
    assert store.resolve(issued.session_token + "forged") is None


def test_expired_and_revoked_sessions_fail_closed(tmp_path: Path) -> None:
    provider, database = _provider(tmp_path)
    user = _provision(provider)
    store = SQLiteSessionStore(database)

    revoked = store.issue(user.id, ttl_seconds=600)
    assert store.revoke(revoked.session_token)
    assert store.resolve(revoked.session_token) is None

    expired = store.issue(user.id, ttl_seconds=600)
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE platform_auth_sessions SET expires_at = ? WHERE session_id = ?",
            (past, expired.session_id),
        )
        connection.commit()
    assert store.resolve(expired.session_token) is None


def test_suspended_user_invalidates_existing_session(tmp_path: Path) -> None:
    provider, database = _provider(tmp_path)
    user = _provision(provider)
    store = SQLiteSessionStore(database)
    service = SessionPrincipalService(provider, store, session_ttl_seconds=600)
    login = service.login("researcher@example.org", "correct horse battery staple")
    assert login is not None
    assert service.resolve(login.session_token) is not None

    provider.set_user_status(user.id, "suspended")
    assert service.resolve(login.session_token) is None
    with sqlite3.connect(database) as connection:
        revoked = connection.execute(
            "SELECT revoked_at FROM platform_auth_sessions WHERE session_id = ?",
            (login.session.principal.session_id,),
        ).fetchone()
    assert revoked is not None
    assert revoked[0] is not None


def test_session_principal_contains_server_loaded_global_roles(tmp_path: Path) -> None:
    provider, database = _provider(tmp_path)
    user = provider.provision_user(
        email="admin@example.org",
        display_name="Infra Admin",
        password="a sufficiently long admin password",
        global_roles={GlobalRole.PLATFORM_ADMIN},
    )
    service = SessionPrincipalService(
        provider,
        SQLiteSessionStore(database),
        session_ttl_seconds=600,
    )
    login = service.login("admin@example.org", "a sufficiently long admin password")
    assert login is not None
    assert login.session.principal.user_id == user.id
    assert login.session.principal.workspace_memberships == ()
    assert login.session.principal.global_roles == frozenset({GlobalRole.PLATFORM_ADMIN})
    assert login.session.principal.session_id.startswith("ses_")


def test_provisioning_cli_never_accepts_password_argument_or_logs_hash() -> None:
    source = (ROOT / "tools" / "provision_nutev_user.py").read_text(encoding="utf-8")
    assert 'getpass("New NutEV password: ")' in source
    assert 'getpass("Confirm NutEV password: ")' in source
    assert 'add_argument("--password"' not in source
    assert "password_hash" not in source
    assert "session_token" not in source


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
        response = urlopen(request, timeout=5)
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        parsed = json.loads(body) if body else {}
        return int(exc.code), parsed, list(exc.headers.get_all("Set-Cookie") or [])
    body = response.read().decode("utf-8")
    parsed = json.loads(body) if body else {}
    return int(response.status), parsed, list(response.headers.get_all("Set-Cookie") or [])


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
def test_auth_pilot_http_login_me_logout_is_cookie_only_and_fail_closed(tmp_path: Path) -> None:
    database = tmp_path / "auth-http.sqlite3"
    password = "correct horse battery staple"
    provider = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    user = provider.provision_user(
        email="researcher@example.org",
        display_name="Researcher",
        password=password,
    )

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

        status, body, _headers = _http(base_url + "/api/auth/me")
        assert status == 401
        assert body["error"] == "authentication_required"

        status, body, _headers = _http(
            base_url + "/api/auth/login",
            method="POST",
            payload={"email": "researcher@example.org", "password": "wrong password value"},
        )
        assert status == 401
        assert body == {"error": "invalid_credentials"}

        status, body, set_cookies = _http(
            base_url + "/api/auth/login",
            method="POST",
            payload={"email": "researcher@example.org", "password": password},
        )
        assert status == 200
        serialized = json.dumps(body, sort_keys=True)
        assert body["authenticated"] is True
        assert body["user"]["id"] == user.id
        assert "password" not in serialized
        assert "session_token" not in serialized
        assert "session_id" not in serialized
        assert len(set_cookies) == 1
        cookie_header = set_cookies[0]
        assert "HttpOnly" in cookie_header
        assert "SameSite=Lax" in cookie_header
        assert "Secure" in cookie_header
        assert "Max-Age=600" in cookie_header

        parsed_cookie = SimpleCookie()
        parsed_cookie.load(cookie_header)
        raw_token = parsed_cookie["nutev_auth_session"].value
        assert raw_token
        request_cookie = f"nutev_auth_session={raw_token}"

        with sqlite3.connect(database) as connection:
            session_row = connection.execute(
                "SELECT token_hash FROM platform_auth_sessions ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
        assert session_row is not None
        assert raw_token != str(session_row[0])
        assert raw_token not in str(session_row[0])

        status, body, _headers = _http(base_url + "/api/auth/me", cookie=request_cookie)
        assert status == 200
        assert body["user"]["id"] == user.id

        status, body, clear_headers = _http(
            base_url + "/api/auth/logout",
            method="POST",
            cookie=request_cookie,
            payload={},
        )
        assert status == 200
        assert body == {"authenticated": False}
        assert any("Max-Age=0" in value for value in clear_headers)

        status, body, _headers = _http(base_url + "/api/auth/me", cookie=request_cookie)
        assert status == 401
        assert body["error"] == "invalid_or_expired_session"

        status, body, _headers = _http(
            base_url + "/api/auth/me",
            cookie="nutev_auth_session=forged-session-token-that-is-long-enough-to-parse",
        )
        assert status == 401
        assert body["error"] == "invalid_or_expired_session"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_secure_server_defaults_to_legacy_and_does_not_store_credentials_in_browser() -> None:
    source = (WEB / "secure_server.py").read_text(encoding="utf-8")
    assert 'os.environ.get("NUTEV_AUTH_MODE") or "legacy"' in source
    assert 'AUTH_SESSION_COOKIE = "nutev_auth_session"' in source
    assert '"HttpOnly"' in source
    assert '"SameSite=Lax"' in source
    assert "localStorage" not in source
    assert "sessionStorage" not in source
    assert '"session_token"' not in source
    serializer = source.split("def _login_response", 1)[1].split("def do_POST", 1)[0]
    assert '"password"' not in serializer
