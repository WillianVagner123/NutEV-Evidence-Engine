"""Read-only Article 1 gate state for the authenticated product surface.

The values come from the canonical repository master state
(``config/nutev/article1_search_master_v1.json``) rather than from anything this module
decides. Nothing here can open a gate: the endpoint reports what the master records and
derives a closed state for every value it does not recognise.

Access follows the surfaces that already exist: pilot mode, an authenticated Principal, the
server-side project context, ``APPLICATION_READ`` on that project, and the server-managed
Article 1 owner pin. A project that is not the pinned Article 1 project gets not-found
semantics, so Article 1 state never leaks into another tenant's project view.
"""
from __future__ import annotations

from http import HTTPStatus
import json
from pathlib import Path
import threading
from urllib.parse import urlparse

from first_party_source_access import article1_source_owner_allowed
from nutev.tenancy import SQLiteWorkspaceProjectStore, WorkspaceProjectService
from nutev.tenancy.permissions import Permission, PermissionDenied, PermissionService
from server import APP_ROOT, NutEVHandler

_LOCK = threading.Lock()
_ACCESS: WorkspaceProjectService | None = None
_INSTALLED = False

_MASTER_PATH = APP_ROOT.parents[1] / "config" / "nutev" / "article1_search_master_v1.json"

# A PRESS record only reads as passed when the master says exactly that. Every other value,
# including an unknown one, stays PENDING so a malformed or future state never reads as open.
_PRESS_PASS = "PASS"


def _platform_database() -> Path:
    import os

    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "auth.sqlite3").resolve()


def _access() -> WorkspaceProjectService:
    global _ACCESS
    with _LOCK:
        if _ACCESS is None:
            _ACCESS = WorkspaceProjectService(SQLiteWorkspaceProjectStore(_platform_database()))
        return _ACCESS


def _pilot_enabled(handler: NutEVHandler) -> bool:
    enabled = getattr(handler, "_auth_pilot_enabled", None)
    if not callable(enabled) or not enabled():
        handler._json({"error": "auth_pilot_disabled"}, HTTPStatus.NOT_FOUND)
        return False
    return True


def _project_context(handler: NutEVHandler):
    if not _pilot_enabled(handler):
        return None
    resolver = getattr(handler, "_tenant_search_session", None)
    if not callable(resolver):
        handler._json({"error": "authentication_required"}, HTTPStatus.UNAUTHORIZED)
        return None
    resolved = resolver()
    if resolved is None:
        return None
    session, snapshot = resolved
    current = snapshot.current
    if not current.workspace_id or not current.project_id:
        handler._json({"error": "project_context_required"}, HTTPStatus.CONFLICT)
        return None
    return session.principal, current.workspace_id, current.project_id


def _load_master() -> dict:
    with _MASTER_PATH.open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError("article1 master state is not an object")
    return payload


def _section(master: dict, key: str) -> dict:
    value = master.get(key)
    return value if isinstance(value, dict) else {}


def _gates(master: dict) -> list[dict[str, object]]:
    """Derive the gate list from recorded master values, never from literals.

    Each gate reports the raw recorded value alongside the derived state so an audit reader can
    see the source, and so a future master that records a passed gate is reflected rather than
    overridden here.
    """
    formal = _section(master, "formal_search")
    discovery = _section(_section(master, "production_snapshot"), "discovery")

    discovery_recorded = str(discovery.get("status") or "")
    press_recorded = str(formal.get("press_status") or "")
    gf10_recorded = bool(formal.get("gf10_authorized"))
    freeze_recorded = bool(formal.get("query_freeze_complete"))
    search_recorded = bool(formal.get("formal_provider_search_executed"))
    prisma_recorded = bool(formal.get("prisma_search_event_emitted"))

    return [
        {
            "key": "discovery",
            "state": "COMPLETE" if discovery_recorded.startswith("COMPLETE") else "PENDING",
            "recorded_value": discovery_recorded,
            "open": False,
            "note": "discovery_harvest_is_not_a_prisma_search",
        },
        {
            "key": "press",
            "state": "PASS" if press_recorded == _PRESS_PASS else "PENDING",
            "recorded_value": press_recorded,
            "open": press_recorded == _PRESS_PASS,
        },
        {
            "key": "gf10",
            "state": "AUTHORIZED" if gf10_recorded else "NOT_AUTHORIZED",
            "recorded_value": gf10_recorded,
            "open": gf10_recorded,
        },
        {
            "key": "query_freeze",
            "state": "COMPLETE" if freeze_recorded else "PENDING",
            "recorded_value": freeze_recorded,
            "open": freeze_recorded,
        },
        {
            "key": "formal_search",
            "state": "EXECUTED" if search_recorded else "NOT_EXECUTED",
            "recorded_value": search_recorded,
            "open": search_recorded,
        },
        {
            "key": "prisma",
            "state": "CREATED" if prisma_recorded else "NOT_CREATED",
            "recorded_value": prisma_recorded,
            "open": prisma_recorded,
        },
    ]


def _discovery_corpus(master: dict) -> dict[str, object]:
    snapshot = _section(master, "production_snapshot")
    discovery = _section(snapshot, "discovery")
    deepening = _section(snapshot, "tier_a_deepening")
    return {
        "captured_at": snapshot.get("captured_at"),
        "search_id": master.get("production_search_id"),
        "records_before_dedup": discovery.get("records_before_dedup"),
        "unique_references": discovery.get("unique_references"),
        "accepted_structural_records": discovery.get("accepted_structural_records"),
        "structurally_quarantined_records": discovery.get("structurally_quarantined_records"),
        "tier_a_records": deepening.get("records"),
        "tier_a_retrieved_or_partial": deepening.get("retrieved_or_partial"),
        # Restated with the payload so no consumer can read these as screening or PRISMA numbers.
        "counts_are_discovery_not_prisma": True,
        "counts_are_not_inclusion": True,
    }


def _scientific_state(handler: NutEVHandler) -> bool:
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved

    if not article1_source_owner_allowed(workspace_id, project_id):
        handler._json({"error": "article1_project_not_found"}, HTTPStatus.NOT_FOUND)
        return True

    try:
        context = _access().authorization_context(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        PermissionService().require(principal, Permission.APPLICATION_READ, context=context)
    except PermissionDenied:
        handler._json({"error": "application_read_required"}, HTTPStatus.FORBIDDEN)
        return True
    except (KeyError, PermissionError, ValueError):
        handler._json({"error": "article1_project_not_found"}, HTTPStatus.NOT_FOUND)
        return True

    try:
        master = _load_master()
    except (OSError, ValueError):
        handler._json({"error": "article1_master_state_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True

    handler._json(
        {
            "status": master.get("status"),
            "master_version": master.get("master_version"),
            "question": master.get("question"),
            "gates": _gates(master),
            "discovery_corpus": _discovery_corpus(master),
            "historical_binding": {
                # The owner pin is server-managed configuration, which is what scopes access to
                # the historical Article 1 material. It is an access binding only: it adopts no
                # screening, eligibility, PRISMA or reviewer decision into this project.
                "mechanism": "server_managed_owner_pin",
                "state": "ACTIVE",
                "adopts_scientific_decisions": False,
                "adopts_prisma_state": False,
            },
            "boundaries": {
                "state_is_read_only_here": True,
                "gate_cannot_be_opened_from_this_surface": True,
                "supervisor_access_is_not_approval": True,
                "rank_is_not_evidence_quality": True,
                "retrieval_is_not_inclusion": True,
            },
            "source": "config/nutev/article1_search_master_v1.json",
        }
    )
    return True


def _article1_state_get(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/article1/scientific-state":
        return _scientific_state(handler)
    return False


def install_article1_state_routes() -> None:
    """Install the read-only Article 1 gate-state route."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    original_get = NutEVHandler.do_GET

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _article1_state_get(self, parsed):
            return
        original_get(self)

    NutEVHandler.do_GET = do_get
