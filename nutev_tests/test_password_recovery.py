from __future__ import annotations

from pathlib import Path
import sqlite3

from nutev.tenancy import SQLiteAuthProvider, SQLiteSessionStore
from nutev.tenancy.password_reset import SQLitePasswordResetStore


def test_password_reset_token_is_hash_only_and_single_use(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    provider = SQLiteAuthProvider(database)
    user = provider.provision_user(
        email="researcher@example.org",
        display_name="Researcher",
        password="original sufficiently long password",
    )
    store = SQLitePasswordResetStore(database)
    ticket = store.issue("researcher@example.org")
    assert ticket is not None
    assert store.inspect(ticket.token) is not None

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT token_hash FROM platform_auth_password_resets WHERE id = ?",
            (ticket.reset.id,),
        ).fetchone()
    assert row is not None
    persisted = str(row[0])
    assert ticket.token not in persisted
    assert len(persisted) == 64

    changed = store.consume(ticket.token, password="new sufficiently long password")
    assert changed.id == user.id
    assert store.inspect(ticket.token) is None
    assert provider.authenticate("researcher@example.org", "original sufficiently long password") is None
    assert provider.authenticate("researcher@example.org", "new sufficiently long password") is not None


def test_fresh_reset_invalidates_previous_link(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    SQLiteAuthProvider(database).provision_user(
        email="researcher@example.org",
        display_name="Researcher",
        password="original sufficiently long password",
    )
    store = SQLitePasswordResetStore(database)
    first = store.issue("researcher@example.org")
    second = store.issue("researcher@example.org")
    assert first is not None and second is not None
    assert first.token != second.token
    assert store.inspect(first.token) is None
    assert store.inspect(second.token) is not None


def test_password_change_revokes_active_sessions(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    provider = SQLiteAuthProvider(database)
    user = provider.provision_user(
        email="researcher@example.org",
        display_name="Researcher",
        password="original sufficiently long password",
    )
    sessions = SQLiteSessionStore(database)
    issued = sessions.issue(user.id)
    assert sessions.resolve(issued.session_token) is not None

    reset = SQLitePasswordResetStore(database).issue("researcher@example.org")
    assert reset is not None
    SQLitePasswordResetStore(database).consume(reset.token, password="new sufficiently long password")
    assert sessions.resolve(issued.session_token) is None


def test_unknown_email_does_not_create_reset_record(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    store = SQLitePasswordResetStore(database)
    assert store.issue("missing@example.org") is None
    with sqlite3.connect(database) as connection:
        count = connection.execute("SELECT COUNT(*) FROM platform_auth_password_resets").fetchone()[0]
    assert count == 0


def test_recovery_pages_and_public_boundary_are_present() -> None:
    root = Path(__file__).resolve().parents[1]
    web = root / "apps" / "nutev-web"
    login = (web / "login.html").read_text(encoding="utf-8")
    forgot = (web / "forgot-password.html").read_text(encoding="utf-8")
    reset = (web / "reset-password.html").read_text(encoding="utf-8")
    boundary = (web / "request_boundary.py").read_text(encoding="utf-8")
    api = (web / "access_request_api.py").read_text(encoding="utf-8")

    assert 'href="/forgot-password.html"' in login
    assert "forgot-password.js" in forgot
    assert "reset-password.js" in reset
    assert '"/api/auth/password-reset"' in boundary
    assert "/api/auth/password-reset/request" in api
    assert "/api/auth/password-reset/confirm" in api
    assert "send_access_approved_email" in api
