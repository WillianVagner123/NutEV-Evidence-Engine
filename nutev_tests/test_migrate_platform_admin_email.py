from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from argon2 import PasswordHasher

from nutev.tenancy import GlobalRole, SQLiteAuthProvider, SQLiteSessionStore

ROOT = Path(__file__).resolve().parents[1]


def _run(database: Path, source_email: str, target_email: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "migrate_platform_admin_email.py"),
            "--database",
            str(database),
            "--from-email",
            source_email,
            "--to-email",
            target_email,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _provider(database: Path) -> SQLiteAuthProvider:
    return SQLiteAuthProvider(
        database,
        password_hasher=PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1),
    )


def test_migration_preserves_identity_password_roles_and_session(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    provider = _provider(database)
    password = "correct horse battery staple"
    user = provider.provision_user(
        email="legacy-admin@example.org",
        display_name="Bootstrap Admin",
        password=password,
        global_roles=(GlobalRole.PLATFORM_ADMIN,),
    )
    session_store = SQLiteSessionStore(database)
    issued = session_store.issue(user.id, ttl_seconds=3600)

    with sqlite3.connect(database) as connection:
        before = connection.execute(
            """
            SELECT id, email, display_name, password_hash, status,
                   global_roles_json, created_at, last_login_at
            FROM platform_auth_users WHERE id = ?
            """,
            (user.id,),
        ).fetchone()
    assert before is not None

    first = _run(database, "LEGACY-ADMIN@example.org", "current-admin@example.org")
    assert first.returncode == 0, first.stderr
    payload = json.loads(first.stdout)
    assert payload == {
        "changed": True,
        "credentials_modified": False,
        "scientific_state_modified": False,
        "status": "platform_admin_email_migrated",
        "user_id_preserved": True,
        "workspace_or_project_access_modified": False,
    }

    with sqlite3.connect(database) as connection:
        after = connection.execute(
            """
            SELECT id, email, display_name, password_hash, status,
                   global_roles_json, created_at, last_login_at
            FROM platform_auth_users WHERE id = ?
            """,
            (user.id,),
        ).fetchone()
    assert after is not None
    assert after[0] == before[0]
    assert after[1] == "current-admin@example.org"
    assert after[2:] == before[2:]

    authenticated = provider.authenticate("current-admin@example.org", password)
    assert authenticated is not None
    assert authenticated.user.id == user.id
    assert GlobalRole.PLATFORM_ADMIN in authenticated.global_roles
    assert provider.authenticate("legacy-admin@example.org", password) is None

    resolved = session_store.resolve(issued.session_token)
    assert resolved is not None
    assert resolved.user_id == user.id

    second = _run(database, "legacy-admin@example.org", "current-admin@example.org")
    assert second.returncode == 0, second.stderr
    second_payload = json.loads(second.stdout)
    assert second_payload["status"] == "already_migrated"
    assert second_payload["changed"] is False


def test_migration_is_noop_when_legacy_source_is_absent(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    provider = _provider(database)
    provider.provision_user(
        email="researcher@example.org",
        display_name="Researcher",
        password="correct horse battery staple",
    )

    result = _run(database, "legacy-admin@example.org", "current-admin@example.org")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "legacy_source_absent"
    assert payload["changed"] is False


def test_migration_refuses_target_conflict(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    provider = _provider(database)
    provider.provision_user(
        email="legacy-admin@example.org",
        display_name="Bootstrap Admin",
        password="correct horse battery staple",
        global_roles=(GlobalRole.PLATFORM_ADMIN,),
    )
    provider.provision_user(
        email="current-admin@example.org",
        display_name="Different Identity",
        password="another correct horse battery staple",
    )

    result = _run(database, "legacy-admin@example.org", "current-admin@example.org")
    assert result.returncode == 4
    payload = json.loads(result.stdout)
    assert payload["status"] == "target_email_conflict"
    assert payload["changed"] is False


def test_migration_refuses_non_admin_source(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    provider = _provider(database)
    provider.provision_user(
        email="legacy-admin@example.org",
        display_name="Not Admin",
        password="correct horse battery staple",
    )

    result = _run(database, "legacy-admin@example.org", "current-admin@example.org")
    assert result.returncode == 8
    payload = json.loads(result.stdout)
    assert payload["status"] == "legacy_source_not_platform_admin"
    assert payload["changed"] is False
