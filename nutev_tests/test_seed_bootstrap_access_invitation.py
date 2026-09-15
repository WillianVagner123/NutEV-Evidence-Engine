from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

from nutev.tenancy import GlobalRole, SQLiteAuthProvider, initialize_platform_database
from nutev.tenancy.access_requests import SQLiteAccessRequestStore

ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "src"), str(ROOT)])
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / script), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_seeded_invitation_keeps_raw_token_out_of_database_and_password_user_owned(
    tmp_path: Path,
) -> None:
    database = tmp_path / "auth.sqlite3"
    initialize_platform_database(database)
    raw_token = "bootstrap-test-token-that-is-long-enough-123456789"
    digest = sha256(raw_token.encode("utf-8")).hexdigest()

    seeded = _run(
        "seed_bootstrap_access_invitation.py",
        "--database",
        str(database),
        "--email",
        "admin@example.org",
        "--display-name",
        "First Admin",
        "--institution",
        "NutEV",
        "--intended-use",
        "First platform administrator bootstrap for governed access.",
        "--token-digest",
        digest,
    )
    assert seeded.returncode == 0, seeded.stderr
    seeded_payload = json.loads(seeded.stdout)
    assert seeded_payload["status"] == "bootstrap_invitation_seeded"
    assert seeded_payload["raw_token_persisted"] is False
    assert seeded_payload["password_created"] is False
    assert seeded_payload["platform_admin_granted"] is False

    store = SQLiteAccessRequestStore(database)
    record = store.inspect_invitation(raw_token)
    assert record is not None
    assert record.email == "admin@example.org"
    assert record.status == "approved"
    assert record.decided_by == "operator-bootstrap-first-platform-admin"

    with sqlite3.connect(database) as connection:
        persisted = connection.execute(
            "SELECT invitation_token_hash FROM platform_access_requests WHERE id = ?",
            (record.id,),
        ).fetchone()
    assert persisted is not None
    assert persisted[0] == digest
    assert persisted[0] != raw_token

    password = "the invited person chooses this password"
    user = store.accept_invitation(raw_token, password=password)
    provider = SQLiteAuthProvider(database)
    subject = provider.authenticate("admin@example.org", password)
    assert subject is not None
    assert subject.user.id == user.id
    assert subject.global_roles == frozenset()

    grant = _run(
        "grant_platform_admin.py",
        "--database",
        str(database),
        "--email",
        "admin@example.org",
    )
    assert grant.returncode == 0, grant.stderr
    grant_payload = json.loads(grant.stdout)
    assert grant_payload["status"] == "platform_admin_granted"
    assert grant_payload["workspace_or_project_access_granted"] is False
    assert grant_payload["scientific_state_modified"] is False

    promoted = provider.authenticate("admin@example.org", password)
    assert promoted is not None
    assert promoted.global_roles == frozenset({GlobalRole.PLATFORM_ADMIN})


def test_seed_refuses_invalid_digest_and_existing_user(tmp_path: Path) -> None:
    database = tmp_path / "auth.sqlite3"
    initialize_platform_database(database)

    invalid = _run(
        "seed_bootstrap_access_invitation.py",
        "--database",
        str(database),
        "--email",
        "admin@example.org",
        "--display-name",
        "First Admin",
        "--institution",
        "NutEV",
        "--intended-use",
        "First platform administrator bootstrap for governed access.",
        "--token-digest",
        "not-a-sha256-digest",
    )
    assert invalid.returncode == 2
    assert json.loads(invalid.stdout)["status"] == "invalid_token_digest"

    provider = SQLiteAuthProvider(database)
    provider.provision_user(
        email="admin@example.org",
        display_name="First Admin",
        password="a sufficiently long password",
    )
    digest = sha256(b"another-long-bootstrap-test-token-123456789").hexdigest()
    existing = _run(
        "seed_bootstrap_access_invitation.py",
        "--database",
        str(database),
        "--email",
        "admin@example.org",
        "--display-name",
        "First Admin",
        "--institution",
        "NutEV",
        "--intended-use",
        "First platform administrator bootstrap for governed access.",
        "--token-digest",
        digest,
    )
    assert existing.returncode == 4
    payload = json.loads(existing.stdout)
    assert payload["status"] == "existing_user_requires_role_grant"
    assert payload["platform_admin_granted"] is False
