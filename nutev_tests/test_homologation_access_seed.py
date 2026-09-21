"""Contract for the provisional homologation seed used to validate supervisor access.

Two layers are covered:

* the seeder's fail-closed guardrails, so a homologation convenience can never be
  pointed at production identity state;
* the real HTTP journey of a seeded ``ACADEMIC_SUPERVISOR`` against a live pilot
  server, so the read-only envelope is proven at the boundary a person actually
  uses, not only in the permission service.
"""
from __future__ import annotations

from contextlib import contextmanager
import http.client
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "seed_homologation_access.py"
SPEC = importlib.util.spec_from_file_location("seed_homologation_access", MODULE_PATH)
assert SPEC and SPEC.loader
seeder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = seeder
SPEC.loader.exec_module(seeder)


def _run_seeder(argv: list[str], capsys, *, environment: str | None = "homologacao"):
    previous = os.environ.get("NUTEV_ENVIRONMENT")
    if environment is None:
        os.environ.pop("NUTEV_ENVIRONMENT", None)
    else:
        os.environ["NUTEV_ENVIRONMENT"] = environment
    try:
        code = seeder.main(argv)
    finally:
        if previous is None:
            os.environ.pop("NUTEV_ENVIRONMENT", None)
        else:
            os.environ["NUTEV_ENVIRONMENT"] = previous
    return code, json.loads(capsys.readouterr().out)


def test_seeder_refuses_when_environment_is_unset_or_production(tmp_path, capsys) -> None:
    target = tmp_path / "homologacao.sqlite3"

    code, payload = _run_seeder(["--database", str(target)], capsys, environment=None)
    assert code == 2
    assert payload["status"] == "refused_production_environment"
    assert payload["seeded"] is False
    assert not target.exists()

    code, payload = _run_seeder(["--database", str(target)], capsys, environment="production")
    assert code == 2
    assert payload["status"] == "refused_production_environment"
    assert not target.exists()


def test_seeder_refuses_the_canonical_production_database_path(tmp_path, capsys) -> None:
    production = tmp_path / "project_output_reference" / "platform" / "auth.sqlite3"
    production.parent.mkdir(parents=True)

    code, payload = _run_seeder(["--database", str(production)], capsys)
    assert code == 3
    assert payload["status"] == "refused_production_database_path"
    assert not production.exists()


def test_seeder_refuses_the_configured_auth_database(tmp_path, capsys, monkeypatch) -> None:
    configured = tmp_path / "live.sqlite3"
    monkeypatch.setenv("NUTEV_AUTH_DB", str(configured))

    code, payload = _run_seeder(["--database", str(configured)], capsys)
    assert code == 3
    assert payload["status"] == "refused_production_database_path"


def test_seeder_refuses_a_database_that_already_holds_identities(tmp_path, capsys) -> None:
    target = tmp_path / "homologacao.sqlite3"
    assert _run_seeder(["--database", str(target)], capsys)[0] == 0

    code, payload = _run_seeder(["--database", str(target)], capsys)
    assert code == 5
    assert payload["status"] == "refused_populated_database"
    assert payload["existing_identity_count"] >= 2


def test_seed_creates_tenancy_state_only_with_disposable_credentials(tmp_path, capsys) -> None:
    target = tmp_path / "homologacao.sqlite3"
    code, payload = _run_seeder(["--database", str(target)], capsys)

    assert code == 0
    assert payload["status"] == "homologation_seeded"
    assert payload["supervisor"]["role"] == "ACADEMIC_SUPERVISOR"
    assert payload["scientific_state_modified"] is False
    assert payload["prisma_press_or_gf10_state_created"] is False
    assert payload["owner"]["password"] != payload["supervisor"]["password"]

    with sqlite3.connect(target) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        stored = connection.execute(
            "SELECT password_hash FROM platform_auth_users"
        ).fetchall()
        projects = connection.execute("SELECT COUNT(*) FROM platform_projects").fetchone()[0]

    # The seed is tenancy/navigation state; no scientific payload table is created here.
    assert "platform_workspace_memberships" in tables
    assert projects == 1
    raw_passwords = {payload["owner"]["password"], payload["supervisor"]["password"]}
    for (stored_hash,) in stored:
        assert str(stored_hash) not in raw_passwords
        assert str(stored_hash).startswith("$argon2")


# --- live HTTP journey -------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _call(base: str, path: str, method: str = "GET", body=None, cookie: str = ""):
    address = urlsplit(base)
    connection = http.client.HTTPConnection(address.hostname, address.port, timeout=10)
    headers = {"Cookie": cookie, "Origin": base}
    if body is not None:
        headers["Content-Type"] = "application/json"
    connection.request(method, path, None if body is None else json.dumps(body), headers)
    response = connection.getresponse()
    raw = response.read()
    result = (response.status, raw, dict(response.getheaders()))
    connection.close()
    return result


def _login(base: str, email: str, password: str) -> str:
    status, raw, headers = _call(base, "/api/auth/login", "POST", {"email": email, "password": password})
    assert status == 200, raw
    return headers["Set-Cookie"].split(";")[0]


@contextmanager
def _homologation_server(tmp_path: Path, capsys):
    target = tmp_path / "homologacao.sqlite3"
    code, seed = _run_seeder(["--database", str(target)], capsys)
    assert code == 0

    port = _free_port()
    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join([str(ROOT / "src"), str(ROOT)]),
        "NUTEV_AUTH_MODE": "pilot",
        "NUTEV_ENVIRONMENT": "homologacao",
        "NUTEV_AUTH_DB": str(target),
        "NUTEV_DISABLE_NETWORK": "1",
        "NUTEV_SEARCH_FULLTEXT_LIMIT": "0",
        "NUTEV_BUILD_COMMIT": "homologation-only-not-production",
    }
    log_path = tmp_path / "server.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "apps" / "nutev-web" / "secure_server.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=ROOT,
            env=environment,
            stdout=log,
            stderr=log,
        )
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                try:
                    if _call(base, "/api/health")[0] == 200:
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError(log_path.read_text())
            yield base, seed
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def test_seeded_supervisor_completes_the_real_login_journey_read_only(tmp_path, capsys) -> None:
    with _homologation_server(tmp_path, capsys) as (base, seed):
        supervisor = seed["supervisor"]
        owner = seed["owner"]
        workspace_id = seed["workspace"]["id"]
        project_id = seed["project"]["id"]

        assert _call(
            base,
            "/api/auth/login",
            "POST",
            {"email": supervisor["email"], "password": "senha-errada"},
        )[0] == 401

        cookie = _login(base, supervisor["email"], supervisor["password"])
        status, raw, _ = _call(base, "/api/auth/me", cookie=cookie)
        assert status == 200
        me = json.loads(raw)
        assert me["authenticated"] is True
        assert me["global_roles"] == []
        assert me["workspace_memberships"] == [
            {"workspace_id": workspace_id, "role": "ACADEMIC_SUPERVISOR", "status": "active"}
        ]

        status, raw, _ = _call(
            base,
            "/api/context/select",
            "POST",
            {"workspace_id": workspace_id, "project_id": project_id},
            cookie,
        )
        assert status == 200
        context = json.loads(raw)
        assert context["current"]["project_id"] == project_id
        assert [item["id"] for item in context["projects"]] == [project_id]
        assert context["selection_is_authorization"] is False

        # Read-only envelope enforced at the HTTP boundary.
        status, raw, _ = _call(
            base,
            "/api/search/jobs",
            "POST",
            {"query": "nutrition", "providers": ["pubmed"], "limit": 1},
            cookie,
        )
        assert status == 403, raw

        # The same endpoint accepts a role that does hold SEARCH_RUN, so the 403
        # above is the supervisor's role and not a broken or disabled route.
        owner_cookie = _login(base, owner["email"], owner["password"])
        _call(
            base,
            "/api/context/select",
            "POST",
            {"workspace_id": workspace_id, "project_id": project_id},
            owner_cookie,
        )
        status, raw, _ = _call(
            base,
            "/api/search/jobs",
            "POST",
            {"query": "nutrition", "providers": ["pubmed"], "limit": 1},
            owner_cookie,
        )
        assert status == 202, raw


def test_seeded_supervisor_cannot_reach_an_unauthorized_target(tmp_path, capsys) -> None:
    with _homologation_server(tmp_path, capsys) as (base, seed):
        cookie = _login(base, seed["supervisor"]["email"], seed["supervisor"]["password"])
        foreign_workspace = "wsp_" + "0" * 32
        foreign_project = "prj_" + "0" * 32

        status, _, _ = _call(
            base,
            "/api/context/select",
            "POST",
            {"workspace_id": foreign_workspace, "project_id": foreign_project},
            cookie,
        )
        assert status in {403, 404}

        status, raw, _ = _call(base, "/api/context", cookie=cookie)
        assert status == 200
        context = json.loads(raw)
        assert [item["id"] for item in context["workspaces"]] == [seed["workspace"]["id"]]
