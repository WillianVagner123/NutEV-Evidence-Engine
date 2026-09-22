"""Temporary offline fixture for the doctorate owner / academic supervisor scenario.

Two actors share one workspace: the researcher who owns it and an academic supervisor
holding the read-only ``ACADEMIC_SUPERVISOR`` role. A second, unrelated workspace exists so
cross-tenant probes have a real foreign target rather than an invented ID.

This is not a provisioning endpoint and it never touches a production path. It creates
tenancy and navigation state only: no scientific record, search, Evidence Library, human
review, PRISMA, PRESS or GF-10, and no approval of any of them. The fixture identities are
disposable and belong to a disposable database.
"""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from argon2 import PasswordHasher

from nutev.tenancy import (
    ApplicationService,
    Principal,
    SCOPING_REVIEW,
    SQLiteApplicationStore,
    SQLiteAuthProvider,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    WorkspaceRole,
    new_opaque_id,
)

ROOT = Path(__file__).resolve().parents[1]

# The fixture supervisor is a stand-in, never a real person's name or address.
OWNER_EMAIL = "responsavel@example.invalid"
OWNER_PASSWORD = "fixture-only responsavel long password 456"
SUPERVISOR_EMAIL = "orientador@example.invalid"
SUPERVISOR_PASSWORD = "fixture-only orientador long password 456"
OUTSIDER_EMAIL = "externo@example.invalid"
OUTSIDER_PASSWORD = "fixture-only externo long password 456"

A1_ASSEMBLY_ID = "WILLIAN_DOCTORATE_A1"


def _principal(user_id: str, access: WorkspaceProjectService) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(access.memberships_for_user(user_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )


def seed(root: Path) -> dict:
    database = root / "platform.sqlite3"
    auth = SQLiteAuthProvider(
        database, password_hasher=PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)
    )
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    applications = ApplicationService(SQLiteApplicationStore(database), access)

    owner = auth.provision_user(
        email=OWNER_EMAIL, display_name="Responsavel do Doutorado", password=OWNER_PASSWORD
    )
    supervisor = auth.provision_user(
        email=SUPERVISOR_EMAIL, display_name="Professor Orientador", password=SUPERVISOR_PASSWORD
    )
    outsider = auth.provision_user(
        email=OUTSIDER_EMAIL, display_name="Workspace Externo", password=OUTSIDER_PASSWORD
    )

    workspace = access.provision_workspace(
        owner_user_id=owner.id, name="Doutorado (fixture)", slug="doutorado-fixture"
    )
    foreign = access.provision_workspace(
        owner_user_id=outsider.id, name="Outro workspace (fixture)", slug="outro-fixture"
    )

    owner_principal = _principal(owner.id, access)
    outsider_principal = _principal(outsider.id, access)

    project = access.create_project(
        owner_principal,
        workspace_id=workspace.id,
        name="Artigo 1 (fixture)",
        slug="artigo-1-fixture",
        description="Cenario de fixture para o fluxo responsavel/orientador",
        project_type="review",
    )
    foreign_project = access.create_project(
        outsider_principal,
        workspace_id=foreign.id,
        name="Projeto alheio (fixture)",
        slug="projeto-alheio-fixture",
        project_type="review",
    )

    # Configuring the application is project configuration only. It approves no method and
    # opens no gate; the Article 1 gate state stays whatever the canonical master records.
    applications.configure(
        owner_principal,
        workspace_id=workspace.id,
        project_id=project.id,
        template_id=SCOPING_REVIEW,
        configuration={"assembly_id": A1_ASSEMBLY_ID},
    )

    access.add_or_update_member(
        owner_principal,
        workspace_id=workspace.id,
        user_id=supervisor.id,
        role=WorkspaceRole.ACADEMIC_SUPERVISOR,
    )

    return {
        "database": str(database),
        "registry": str(root / "registry.sqlite"),
        "exports": str(root / "exports"),
        "owner": {
            "user_id": owner.id,
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD,
            "workspace_id": workspace.id,
            "project_id": project.id,
        },
        "supervisor": {
            "user_id": supervisor.id,
            "email": SUPERVISOR_EMAIL,
            "password": SUPERVISOR_PASSWORD,
            "workspace_id": workspace.id,
            "project_id": project.id,
        },
        "outsider": {
            "user_id": outsider.id,
            "email": OUTSIDER_EMAIL,
            "password": OUTSIDER_PASSWORD,
            "workspace_id": foreign.id,
            "project_id": foreign_project.id,
        },
        "scientific_state_modified": False,
        "scientific_approval_created": False,
    }


@contextmanager
def doctorate_server():
    """Own and delete a fresh synthetic tree; no external root argument is accepted."""
    with tempfile.TemporaryDirectory(prefix="nutev-doctorate-supervisor-") as temp:
        root = Path(temp)
        data = seed(root)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        env = {
            **os.environ,
            "PYTHONPATH": os.pathsep.join([str(ROOT / "src"), str(ROOT)]),
            "NUTEV_AUTH_MODE": "pilot",
            "NUTEV_AUTH_DB": data["database"],
            "NUTEV_REGISTRY_DB": data["registry"],
            "NUTEV_EXPORT_ROOT": data["exports"],
            "NUTEV_ENVIRONMENT": "test",
            "NUTEV_DISABLE_NETWORK": "1",
            "NUTEV_SEARCH_FULLTEXT_LIMIT": "0",
            "NUTEV_BUILD_COMMIT": "fixture-only-not-production",
            # The server-managed Article 1 owner pin is the binding mechanism the product
            # already uses. Pointing it at the fixture project lets the gate panel render
            # without adopting any historical scientific state.
            "NUTEV_A1_WORKSPACE_ID": data["owner"]["workspace_id"],
            "NUTEV_A1_PROJECT_ID": data["owner"]["project_id"],
        }
        script = (
            "import sys\n"
            f"sys.path.insert(0,{str(ROOT / 'apps/nutev-web')!r})\n"
            "from secure_server import main\n"
            f"sys.argv=['secure_server','--host','127.0.0.1','--port',{str(port)!r}]\n"
            "raise SystemExit(main())\n"
        )
        log = (root / "server.log").open("w")
        process = subprocess.Popen([sys.executable, "-c", script], cwd=ROOT, env=env, stdout=log, stderr=log)
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(80):
                try:
                    with urlopen(base + "/api/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError((root / "server.log").read_text())
            yield base, data, root
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            log.close()
