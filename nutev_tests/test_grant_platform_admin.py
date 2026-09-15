from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from argon2 import PasswordHasher

from nutev.tenancy import GlobalRole, SQLiteAuthProvider

ROOT = Path(__file__).resolve().parents[1]


def _run(database: Path, email: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "grant_platform_admin.py"),
            "--database",
            str(database),
            "--email",
            email,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_grant_platform_admin_is_idempotent_and_preserves_password(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    provider = SQLiteAuthProvider(
        database,
        password_hasher=PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1),
    )
    user = provider.provision_user(
        email="admin@example.org",
        display_name="Admin Candidate",
        password="correct horse battery staple",
    )

    with sqlite3.connect(database) as connection:
        before_hash = connection.execute(
            "SELECT password_hash FROM platform_auth_users WHERE id = ?", (user.id,)
        ).fetchone()[0]

    first = _run(database, "ADMIN@example.org")
    assert first.returncode == 0, first.stderr
    first_payload = json.loads(first.stdout)
    assert first_payload["status"] == "platform_admin_granted"
    assert first_payload["changed"] is True
    assert first_payload["scientific_state_modified"] is False
    assert first_payload["workspace_or_project_access_granted"] is False
    assert first_payload["global_roles"] == [GlobalRole.PLATFORM_ADMIN.value]

    second = _run(database, "admin@example.org")
    assert second.returncode == 0, second.stderr
    second_payload = json.loads(second.stdout)
    assert second_payload["status"] == "already_platform_admin"
    assert second_payload["changed"] is False

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT password_hash, global_roles_json FROM platform_auth_users WHERE id = ?",
            (user.id,),
        ).fetchone()
    assert row is not None
    assert row[0] == before_hash
    assert json.loads(row[1]) == [GlobalRole.PLATFORM_ADMIN.value]


def test_grant_platform_admin_refuses_missing_user(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    SQLiteAuthProvider(database, password_hasher=PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1))
    # Materialize schema without creating a user.
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE platform_auth_users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                global_roles_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            """
        )

    result = _run(database, "missing@example.org")
    assert result.returncode == 4
    payload = json.loads(result.stdout)
    assert payload["status"] == "user_not_found"
    assert payload["changed"] is False
