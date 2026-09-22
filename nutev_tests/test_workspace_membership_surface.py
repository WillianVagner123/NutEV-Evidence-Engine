"""Workspace member administration as a product surface.

Covers the HTTP membership API that replaces terminal-only membership grants, the
ACADEMIC_SUPERVISOR read/write envelope exercised against the real endpoints rather than
against hidden buttons, and the cross-tenant death tests that use valid foreign IDs.
"""
from __future__ import annotations

from http.cookies import SimpleCookie
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
    ASSIGNABLE_WORKSPACE_ROLES,
    Principal,
    SQLiteAuthProvider,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
    WorkspaceRole,
    new_opaque_id,
)
from nutev.tenancy.access_requests import SQLiteAccessRequestStore
from nutev.tenancy.models import MembershipStatus
from nutev.tenancy.permissions import PermissionDenied

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"

OWNER_EMAIL = "willian.owner@example.org"
OWNER_PASSWORD = "senha longa do responsavel pelo doutorado"
SUPERVISOR_EMAIL = "orientador@example.org"
SUPERVISOR_PASSWORD = "senha longa do professor orientador"
OUTSIDER_EMAIL = "outro.workspace@example.org"
OUTSIDER_PASSWORD = "senha longa de outro workspace inteiro"
NEWCOMER_EMAIL = "recem.chegado@example.org"
NEWCOMER_PASSWORD = "senha longa de quem ainda nao tem membership"


def _fast_hasher() -> PasswordHasher:
    return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


def _principal(user_id: str, access: WorkspaceProjectService) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=tuple(access.memberships_for_user(user_id)),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http(url: str, *, method: str = "GET", payload: dict | None = None, cookie: str = ""):
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
        body = exc.read().decode("utf-8")
        return int(exc.code), json.loads(body) if body else {}
    body = response.read().decode("utf-8")
    return int(response.status), json.loads(body) if body else {}


def _wait_for_server(base_url: str) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            status, _ = _http(base_url + "/api/health")
            if status == 200:
                return
        except (URLError, OSError, TimeoutError):
            pass
        time.sleep(0.1)
    raise AssertionError("secure_server did not become ready")


def _login(base_url: str, email: str, password: str) -> str:
    request = Request(
        base_url + "/api/auth/login",
        data=json.dumps({"email": email, "password": password}).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    response = urlopen(request, timeout=8)
    cookies = list(response.headers.get_all("Set-Cookie") or [])
    parsed = SimpleCookie()
    parsed.load(cookies[0])
    return f"nutev_auth_session={parsed['nutev_auth_session'].value}"


def _select(base_url: str, cookie: str, workspace_id: str, project_id: str) -> tuple[int, dict]:
    return _http(
        base_url + "/api/context/select",
        method="POST",
        cookie=cookie,
        payload={"workspace_id": workspace_id, "project_id": project_id},
    )


def _seed(database: Path) -> dict:
    """Doctorate workspace plus an unrelated foreign workspace used for the death tests."""
    auth = SQLiteAuthProvider(database, password_hasher=_fast_hasher())
    owner = auth.provision_user(email=OWNER_EMAIL, display_name="Responsavel", password=OWNER_PASSWORD)
    supervisor = auth.provision_user(
        email=SUPERVISOR_EMAIL, display_name="Professor Orientador", password=SUPERVISOR_PASSWORD
    )
    outsider = auth.provision_user(email=OUTSIDER_EMAIL, display_name="Outro", password=OUTSIDER_PASSWORD)
    newcomer = auth.provision_user(email=NEWCOMER_EMAIL, display_name="Recem", password=NEWCOMER_PASSWORD)

    store = SQLiteWorkspaceProjectStore(database)
    access = WorkspaceProjectService(store)
    workspace = access.provision_workspace(owner_user_id=owner.id, name="Doutorado", slug="doutorado")
    foreign = access.provision_workspace(owner_user_id=outsider.id, name="Outro", slug="outro")

    owner_principal = _principal(owner.id, access)
    outsider_principal = _principal(outsider.id, access)
    project = access.create_project(
        owner_principal, workspace_id=workspace.id, name="Artigo 1", slug="artigo-1", project_type="review"
    )
    foreign_project = access.create_project(
        outsider_principal, workspace_id=foreign.id, name="Alheio", slug="alheio", project_type="review"
    )
    access.add_or_update_member(
        owner_principal,
        workspace_id=workspace.id,
        user_id=supervisor.id,
        role=WorkspaceRole.ACADEMIC_SUPERVISOR,
    )
    return {
        "auth": auth,
        "store": store,
        "access": access,
        "owner": owner,
        "supervisor": supervisor,
        "outsider": outsider,
        "newcomer": newcomer,
        "workspace": workspace,
        "foreign": foreign,
        "project": project,
        "foreign_project": foreign_project,
    }


@pytest.fixture()
def seeded(tmp_path: Path) -> dict:
    database = tmp_path / "platform.sqlite3"
    fixture = _seed(database)
    fixture["database"] = database
    return fixture


@pytest.fixture()
def server(seeded: dict):
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(
        {
            "NUTEV_AUTH_MODE": "pilot",
            "NUTEV_AUTH_DB": str(seeded["database"]),
            "NUTEV_AUTH_SESSION_TTL_SECONDS": "600",
            "NUTEV_ENVIRONMENT": "production",
            "NUTEV_DISABLE_NETWORK": "1",
            "NUTEV_A1_WORKSPACE_ID": seeded["workspace"].id,
            "NUTEV_A1_PROJECT_ID": seeded["project"].id,
        }
    )
    process = subprocess.Popen(
        [sys.executable, str(WEB / "secure_server.py"), "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server(base_url)
        yield base_url, seeded
    finally:
        process.terminate()
        process.wait(timeout=10)


# --------------------------------------------------------------------------------------
# Service contract
# --------------------------------------------------------------------------------------


def test_member_administration_cannot_demote_the_sitting_workspace_owner(seeded: dict) -> None:
    """Refusing to assign WORKSPACE_OWNER is only half of the ownership boundary.

    Demoting the sitting owner is the same transfer seen from the other side: it would leave
    the workspace with an owner_user_id whose membership no longer carries owner authority.
    """
    access = seeded["access"]
    workspace = seeded["workspace"]
    owner = seeded["owner"]
    admin_id = seeded["newcomer"].id
    access.add_or_update_member(
        _principal(owner.id, access),
        workspace_id=workspace.id,
        user_id=admin_id,
        role=WorkspaceRole.WORKSPACE_ADMIN,
    )

    with pytest.raises(ValueError):
        access.add_or_update_member(
            _principal(admin_id, access),
            workspace_id=workspace.id,
            user_id=owner.id,
            role=WorkspaceRole.VIEWER,
        )

    assert seeded["store"].active_membership(owner.id, workspace.id).role is WorkspaceRole.WORKSPACE_OWNER


def test_workspace_owner_role_is_never_assignable(seeded: dict) -> None:
    assert WorkspaceRole.WORKSPACE_OWNER not in ASSIGNABLE_WORKSPACE_ROLES
    access = seeded["access"]
    with pytest.raises(ValueError):
        access.add_or_update_member(
            _principal(seeded["owner"].id, access),
            workspace_id=seeded["workspace"].id,
            user_id=seeded["newcomer"].id,
            role=WorkspaceRole.WORKSPACE_OWNER,
        )


def test_roster_read_requires_members_manage(seeded: dict) -> None:
    access = seeded["access"]
    workspace = seeded["workspace"]
    assert access.list_members(_principal(seeded["owner"].id, access), workspace.id)

    for role in (
        WorkspaceRole.ACADEMIC_SUPERVISOR,
        WorkspaceRole.VIEWER,
        WorkspaceRole.RESEARCHER,
        WorkspaceRole.REVIEWER,
        WorkspaceRole.GUEST_REVIEWER,
    ):
        access.add_or_update_member(
            _principal(seeded["owner"].id, access),
            workspace_id=workspace.id,
            user_id=seeded["newcomer"].id,
            role=role,
        )
        with pytest.raises(PermissionDenied):
            access.list_members(_principal(seeded["newcomer"].id, access), workspace.id)


# --------------------------------------------------------------------------------------
# HTTP surface
# --------------------------------------------------------------------------------------


@pytest.mark.integration_no_network
def test_owner_administers_members_over_http(server) -> None:
    base_url, seeded = server
    cookie = _login(base_url, OWNER_EMAIL, OWNER_PASSWORD)
    assert _select(base_url, cookie, seeded["workspace"].id, seeded["project"].id)[0] == 200

    status, roster = _http(base_url + "/api/workspace/members", cookie=cookie)
    assert status == 200, roster
    assert roster["owner_role_assignable"] is False
    assert roster["membership_creates_identity"] is False
    assert roster["membership_is_scientific_approval"] is False
    assert "WORKSPACE_OWNER" not in roster["assignable_roles"]
    assert "ACADEMIC_SUPERVISOR" in roster["assignable_roles"]

    by_email = {member["email"]: member for member in roster["members"]}
    assert by_email[OWNER_EMAIL]["is_workspace_owner"] is True
    assert by_email[OWNER_EMAIL]["role_editable"] is False
    assert by_email[OWNER_EMAIL]["status_editable"] is False
    assert by_email[SUPERVISOR_EMAIL]["role"] == "ACADEMIC_SUPERVISOR"

    # Granting membership to an existing account never provisions an identity.
    status, granted = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=cookie,
        payload={"email": NEWCOMER_EMAIL, "role": "VIEWER"},
    )
    assert status == 200, granted
    assert granted["status"] == "membership_granted"
    assert granted["user_created"] is False
    assert granted["global_role_granted"] is False
    assert granted["scientific_state_modified"] is False
    assert granted["scientific_approval_created"] is False

    # An unknown address is not a provisioning path.
    status, unknown = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=cookie,
        payload={"email": "ninguem@example.org", "role": "VIEWER"},
    )
    assert status == 404, unknown
    assert unknown["error"] == "active_account_not_found"


@pytest.mark.integration_no_network
def test_role_change_needs_explicit_confirmation_and_owner_is_protected(server) -> None:
    base_url, seeded = server
    cookie = _login(base_url, OWNER_EMAIL, OWNER_PASSWORD)
    _select(base_url, cookie, seeded["workspace"].id, seeded["project"].id)

    status, refused = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=cookie,
        payload={"email": SUPERVISOR_EMAIL, "role": "RESEARCHER"},
    )
    assert status == 409, refused
    assert refused["error"] == "role_change_requires_explicit_confirmation"
    assert refused["current_role"] == "ACADEMIC_SUPERVISOR"

    status, roster = _http(base_url + "/api/workspace/members", cookie=cookie)
    supervisor = next(m for m in roster["members"] if m["email"] == SUPERVISOR_EMAIL)
    assert supervisor["role"] == "ACADEMIC_SUPERVISOR", "a refused change must not mutate anything"

    status, changed = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=cookie,
        payload={"email": SUPERVISOR_EMAIL, "role": "RESEARCHER", "allow_role_change": True},
    )
    assert status == 200, changed
    assert changed["status"] == "role_changed"

    # Ownership never moves through member administration, from either direction.
    status, demote = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=cookie,
        payload={"email": OWNER_EMAIL, "role": "VIEWER", "allow_role_change": True},
    )
    assert status == 409, demote
    assert demote["error"] == "ownership_transfer_not_supported_here"

    status, promote = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=cookie,
        payload={"email": NEWCOMER_EMAIL, "role": "WORKSPACE_OWNER"},
    )
    assert status == 400, promote
    assert promote["error"] in {"role_not_assignable", "invalid_membership_role"}

    status, suspend_owner = _http(
        base_url + "/api/workspace/members/status",
        method="POST",
        cookie=cookie,
        payload={"user_id": seeded["owner"].id, "status": "suspended"},
    )
    assert suspend_owner["error"] == "membership_status_refused"
    assert status == 409


@pytest.mark.integration_no_network
def test_suspending_a_member_stops_their_access(server) -> None:
    base_url, seeded = server
    owner_cookie = _login(base_url, OWNER_EMAIL, OWNER_PASSWORD)
    _select(base_url, owner_cookie, seeded["workspace"].id, seeded["project"].id)

    supervisor_cookie = _login(base_url, SUPERVISOR_EMAIL, SUPERVISOR_PASSWORD)
    assert _select(base_url, supervisor_cookie, seeded["workspace"].id, seeded["project"].id)[0] == 200

    status, suspended = _http(
        base_url + "/api/workspace/members/status",
        method="POST",
        cookie=owner_cookie,
        payload={"user_id": seeded["supervisor"].id, "status": "suspended"},
    )
    assert status == 200, suspended
    assert suspended["scientific_state_modified"] is False

    # Principals are rebuilt from current membership on every request, so the next call fails.
    status, context = _http(base_url + "/api/context", cookie=supervisor_cookie)
    assert status == 200, context
    assert context["workspaces"] == []
    assert _select(base_url, supervisor_cookie, seeded["workspace"].id, seeded["project"].id)[0] != 200


@pytest.mark.integration_no_network
def test_supervisor_can_read_but_never_administers_or_writes(server) -> None:
    base_url, seeded = server
    cookie = _login(base_url, SUPERVISOR_EMAIL, SUPERVISOR_PASSWORD)
    assert _select(base_url, cookie, seeded["workspace"].id, seeded["project"].id)[0] == 200

    # Reads the role is meant to have.
    assert _http(base_url + "/api/application", cookie=cookie)[0] == 200
    assert _http(base_url + "/api/searches", cookie=cookie)[0] == 200

    # Member administration is closed to the supervisor at the endpoint, not only in the UI.
    status, listed = _http(base_url + "/api/workspace/members", cookie=cookie)
    assert status == 403, listed
    assert listed["error"] == "members_manage_required"

    status, granted = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=cookie,
        payload={"email": NEWCOMER_EMAIL, "role": "WORKSPACE_ADMIN"},
    )
    assert status == 403, granted

    status, suspended = _http(
        base_url + "/api/workspace/members/status",
        method="POST",
        cookie=cookie,
        payload={"user_id": seeded["owner"].id, "status": "removed"},
    )
    assert status == 403, suspended

    # Scientific writes stay closed too.
    status, configured = _http(
        base_url + "/api/application",
        method="POST",
        cookie=cookie,
        payload={"template_id": "SCOPING_REVIEW", "configuration": {}},
    )
    assert status in {403, 409}, configured

    roster = seeded["store"].list_memberships(seeded["workspace"].id)
    assert {m.user_id for m in roster} == {seeded["owner"].id, seeded["supervisor"].id}


@pytest.mark.integration_no_network
def test_membership_surface_denies_cross_tenant_targets(server) -> None:
    """Death tests with valid foreign IDs: knowing an ID must never grant reach."""
    base_url, seeded = server
    cookie = _login(base_url, OWNER_EMAIL, OWNER_PASSWORD)
    _select(base_url, cookie, seeded["workspace"].id, seeded["project"].id)

    # A foreign workspace_id in the body is ignored: the server uses session context only.
    status, granted = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=cookie,
        payload={
            "email": NEWCOMER_EMAIL,
            "role": "VIEWER",
            "workspace_id": seeded["foreign"].id,
            "project_id": seeded["foreign_project"].id,
        },
    )
    assert status == 200, granted
    foreign_roster = seeded["store"].list_memberships(seeded["foreign"].id)
    assert seeded["newcomer"].id not in {m.user_id for m in foreign_roster}
    assert seeded["newcomer"].id in {m.user_id for m in seeded["store"].list_memberships(seeded["workspace"].id)}

    # The owner cannot select, and therefore cannot administer, the foreign workspace.
    assert _select(base_url, cookie, seeded["foreign"].id, seeded["foreign_project"].id)[0] != 200

    # A foreign member's user_id is not a handle on them either.
    status, suspended = _http(
        base_url + "/api/workspace/members/status",
        method="POST",
        cookie=cookie,
        payload={"user_id": seeded["outsider"].id, "status": "removed"},
    )
    assert status == 404, suspended
    assert seeded["store"].active_membership(seeded["outsider"].id, seeded["foreign"].id) is not None

    # And the foreign owner sees nothing of this workspace.
    outsider_cookie = _login(base_url, OUTSIDER_EMAIL, OUTSIDER_PASSWORD)
    _select(base_url, outsider_cookie, seeded["foreign"].id, seeded["foreign_project"].id)
    status, roster = _http(base_url + "/api/workspace/members", cookie=outsider_cookie)
    assert status == 200, roster
    assert OWNER_EMAIL not in json.dumps(roster)
    assert SUPERVISOR_EMAIL not in json.dumps(roster)


@pytest.mark.integration_no_network
def test_unauthenticated_and_context_free_requests_fail_closed(server) -> None:
    base_url, seeded = server
    assert _http(base_url + "/api/workspace/members")[0] == 401

    cookie = _login(base_url, NEWCOMER_EMAIL, NEWCOMER_PASSWORD)
    status, body = _http(base_url + "/api/workspace/members", cookie=cookie)
    assert status in {403, 409}, body


# --------------------------------------------------------------------------------------
# Article 1 scientific state
# --------------------------------------------------------------------------------------


@pytest.mark.integration_no_network
def test_article1_scientific_state_reports_the_canonical_closed_gates(server) -> None:
    base_url, seeded = server
    cookie = _login(base_url, OWNER_EMAIL, OWNER_PASSWORD)
    _select(base_url, cookie, seeded["workspace"].id, seeded["project"].id)

    status, state = _http(base_url + "/api/article1/scientific-state", cookie=cookie)
    assert status == 200, state

    master = json.loads((ROOT / "config/nutev/article1_search_master_v1.json").read_text(encoding="utf-8"))
    assert state["status"] == master["status"]
    assert state["source"] == "config/nutev/article1_search_master_v1.json"

    gates = {gate["key"]: gate for gate in state["gates"]}
    assert gates["discovery"]["state"] == "COMPLETE"
    assert gates["press"]["state"] == "PENDING"
    assert gates["gf10"]["state"] == "NOT_AUTHORIZED"
    assert gates["query_freeze"]["state"] == "PENDING"
    assert gates["formal_search"]["state"] == "NOT_EXECUTED"
    assert gates["prisma"]["state"] == "NOT_CREATED"
    assert [gate["key"] for gate in state["gates"] if gate["open"]] == []

    assert state["discovery_corpus"]["counts_are_discovery_not_prisma"] is True
    assert state["discovery_corpus"]["counts_are_not_inclusion"] is True
    assert state["historical_binding"]["adopts_scientific_decisions"] is False
    assert state["historical_binding"]["adopts_prisma_state"] is False
    assert state["boundaries"]["gate_cannot_be_opened_from_this_surface"] is True

    # Reading the state is a read: it must not have moved the master file.
    assert json.loads((ROOT / "config/nutev/article1_search_master_v1.json").read_text(encoding="utf-8")) == master


@pytest.mark.integration_no_network
def test_article1_scientific_state_is_readable_by_the_supervisor_only_on_the_pinned_project(server) -> None:
    base_url, seeded = server
    cookie = _login(base_url, SUPERVISOR_EMAIL, SUPERVISOR_PASSWORD)
    _select(base_url, cookie, seeded["workspace"].id, seeded["project"].id)
    status, state = _http(base_url + "/api/article1/scientific-state", cookie=cookie)
    assert status == 200, state
    assert state["boundaries"]["supervisor_access_is_not_approval"] is True

    # A project that is not the pinned Article 1 project gets not-found semantics.
    outsider_cookie = _login(base_url, OUTSIDER_EMAIL, OUTSIDER_PASSWORD)
    _select(base_url, outsider_cookie, seeded["foreign"].id, seeded["foreign_project"].id)
    status, denied = _http(base_url + "/api/article1/scientific-state", cookie=outsider_cookie)
    assert status == 404, denied
    assert denied["error"] == "article1_project_not_found"


def test_assignable_statuses_never_include_invited() -> None:
    """Member administration grants access to an existing account, so there is no invite state."""
    spec = (WEB / "tenant_membership_api.py").read_text(encoding="utf-8")
    assert "MembershipStatus.INVITED" not in spec
    assert MembershipStatus.INVITED.value == "invited"


@pytest.mark.integration_no_network
def test_governed_onboarding_then_http_grant_completes_the_supervisor_chain(server) -> None:
    """Approval creates an account; membership is still a separate, explicit step.

    The operator CLI already covered this chain. This asserts the same boundary when the
    grant happens through the product surface instead of a terminal.
    """
    base_url, seeded = server
    requests = SQLiteAccessRequestStore(seeded["database"])
    submitted = requests.submit(
        email="novo.orientador@example.org",
        display_name="Prof. Convidado",
        institution="Universidade",
        intended_use="Acompanhamento academico.",
    )
    assert submitted is not None
    invitation = requests.approve(submitted.id, decided_by=seeded["owner"].id)
    password = "senha longa definida pela propria pessoa convidada"
    requests.accept_invitation(invitation.token, password=password)

    # The account exists and can log in, but approval granted no workspace at all.
    invited_cookie = _login(base_url, "novo.orientador@example.org", password)
    status, context = _http(base_url + "/api/context", cookie=invited_cookie)
    assert status == 200, context
    assert context["workspaces"] == []
    assert _select(base_url, invited_cookie, seeded["workspace"].id, seeded["project"].id)[0] != 200

    # The owner grants supervision through the product surface.
    owner_cookie = _login(base_url, OWNER_EMAIL, OWNER_PASSWORD)
    _select(base_url, owner_cookie, seeded["workspace"].id, seeded["project"].id)
    status, granted = _http(
        base_url + "/api/workspace/members",
        method="POST",
        cookie=owner_cookie,
        payload={"email": "novo.orientador@example.org", "role": "ACADEMIC_SUPERVISOR"},
    )
    assert status == 200, granted
    assert granted["member"]["role"] == "ACADEMIC_SUPERVISOR"
    assert granted["scientific_approval_created"] is False

    # Now, and only now, the workspace is reachable — with read access only.
    status, context = _http(base_url + "/api/context", cookie=invited_cookie)
    assert [workspace["id"] for workspace in context["workspaces"]] == [seeded["workspace"].id]
    assert _select(base_url, invited_cookie, seeded["workspace"].id, seeded["project"].id)[0] == 200
    assert _http(base_url + "/api/application", cookie=invited_cookie)[0] == 200
    assert _http(base_url + "/api/workspace/members", cookie=invited_cookie)[0] == 403
