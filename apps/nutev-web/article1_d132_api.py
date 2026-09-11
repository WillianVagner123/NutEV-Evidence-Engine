from __future__ import annotations

from http import HTTPStatus
import os
from pathlib import Path
import threading
from urllib.parse import quote, urlparse

from first_party_source_access import article1_source_owner_allowed
from nutev.applications.willian_doctorate_a1 import D132ConfigurationError, D132Service
from nutev.review import ReviewAccessDenied
from nutev.tenancy import (
    ApplicationService,
    SCOPING_REVIEW,
    SQLiteApplicationStore,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
)
from server import APP_ROOT, NutEVHandler

_SERVICE_LOCK = threading.Lock()
_SERVICE: D132Service | None = None
_APPLICATION_SERVICE: ApplicationService | None = None
_INSTALLED = False

ASSEMBLY_ID = "WILLIAN_DOCTORATE_A1"


def _platform_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "auth.sqlite3").resolve()


def _service() -> D132Service:
    global _SERVICE
    with _SERVICE_LOCK:
        if _SERVICE is None:
            _SERVICE = D132Service(
                repo_root=APP_ROOT.parents[1],
                database_path=_platform_database(),
            )
        return _SERVICE


def _applications() -> ApplicationService:
    global _APPLICATION_SERVICE
    with _SERVICE_LOCK:
        if _APPLICATION_SERVICE is None:
            database = _platform_database()
            access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
            _APPLICATION_SERVICE = ApplicationService(SQLiteApplicationStore(database), access)
        return _APPLICATION_SERVICE


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


def _article1_project_context(handler: NutEVHandler):
    resolved = _project_context(handler)
    if resolved is None:
        return None
    principal, workspace_id, project_id = resolved
    if not article1_source_owner_allowed(workspace_id, project_id):
        handler._json({"error": "article1_project_not_found"}, HTTPStatus.NOT_FOUND)
        return None
    try:
        application = _applications().get(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except (KeyError, PermissionError, ValueError):
        handler._json({"error": "article1_project_not_found"}, HTTPStatus.NOT_FOUND)
        return None
    if application is None:
        handler._json({"error": "article1_application_required"}, HTTPStatus.CONFLICT)
        return None
    descriptor = application.descriptor()
    configuration = descriptor.get("configuration")
    if not isinstance(configuration, dict):
        handler._json({"error": "article1_application_required"}, HTTPStatus.CONFLICT)
        return None
    if descriptor.get("template_id") != SCOPING_REVIEW:
        handler._json({"error": "article1_application_required"}, HTTPStatus.CONFLICT)
        return None
    if configuration.get("assembly_id") != ASSEMBLY_ID:
        handler._json({"error": "article1_application_required"}, HTTPStatus.NOT_FOUND)
        return None
    if configuration.get("d132_config_version") != _service().config().config_version:
        handler._json({"error": "article1_d132_config_mismatch"}, HTTPStatus.CONFLICT)
        return None
    return principal, workspace_id, project_id


def _guest_token(handler: NutEVHandler) -> str:
    bearer = getattr(handler, "_bearer", None)
    return str(bearer() if callable(bearer) else "").strip()


def _require_guest_source_owner(token: str) -> None:
    access = _service().engine.access_for_guest(token)
    if not article1_source_owner_allowed(access.workspace_id, access.project_id):
        raise ReviewAccessDenied("review_access_denied")


def _guest_error(handler: NutEVHandler, exc: Exception) -> None:
    if isinstance(exc, (ReviewAccessDenied, PermissionError)):
        handler._json({"error": "review_access_denied"}, HTTPStatus.UNAUTHORIZED)
    elif isinstance(exc, FileNotFoundError):
        handler._json({"error": "review_not_found"}, HTTPStatus.NOT_FOUND)
    elif isinstance(exc, (ValueError, D132ConfigurationError)):
        handler._json({"error": "invalid_review_request", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
    else:
        raise exc


def _owner_error(handler: NutEVHandler, exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        handler._json({"error": "article1_review_access_denied"}, HTTPStatus.FORBIDDEN)
    elif isinstance(exc, FileNotFoundError):
        handler._json({"error": "article1_review_not_found"}, HTTPStatus.NOT_FOUND)
    elif isinstance(exc, (ValueError, D132ConfigurationError)):
        handler._json({"error": "invalid_article1_review", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
    else:
        raise exc


def _guest_get(handler: NutEVHandler, parsed) -> bool:
    if parsed.path != "/api/article1/d132/review":
        return False
    if not _pilot_enabled(handler):
        return True
    token = _guest_token(handler)
    if not token:
        handler._json({"error": "review_token_required"}, HTTPStatus.UNAUTHORIZED)
        return True
    try:
        _require_guest_source_owner(token)
        payload = _service().guest_payload(token)
    except Exception as exc:
        _guest_error(handler, exc)
        return True
    handler._json(payload)
    return True


def _owner_get(handler: NutEVHandler, parsed) -> bool:
    prefix = "/api/article1/d132/rounds/"
    if not parsed.path.startswith(prefix):
        return False
    resolved = _article1_project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    tail = parsed.path[len(prefix) :].strip("/")
    adjudication = False
    if tail.endswith("/adjudication"):
        tail = tail[: -len("/adjudication")].strip("/")
        adjudication = True
    if not tail or "/" in tail:
        handler._json({"error": "article1_review_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    try:
        if adjudication:
            payload = _service().adjudication_payload(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                project_access_confirmed=True,
                round_id=tail,
            )
        else:
            payload = _service().summary(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                project_access_confirmed=True,
                round_id=tail,
            )
    except Exception as exc:
        _owner_error(handler, exc)
        return True
    handler._json(payload)
    return True


def _article1_get(handler: NutEVHandler, parsed) -> bool:
    return _guest_get(handler, parsed) or _owner_get(handler, parsed)


def _create_round(handler: NutEVHandler) -> bool:
    resolved = _article1_project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        state = _service().create_round(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
        )
        payload = _service().summary(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=state.round_id,
        )
    except Exception as exc:
        _owner_error(handler, exc)
        return True
    handler._json(payload, HTTPStatus.CREATED)
    return True


def _issue_guest(handler: NutEVHandler) -> bool:
    resolved = _article1_project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        body = handler._read_json()
        round_id = str(body.get("round_id") or "").strip()
        slot = str(body.get("slot") or "").strip()
        label = str(body.get("label") or "").strip()
        ttl_raw = body.get("ttl_seconds")
        ttl = int(ttl_raw) if ttl_raw is not None else None
        issued = _service().issue_guest_reviewer(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_id,
            slot=slot,
            label=label,
            ttl_seconds=ttl,
        )
    except Exception as exc:
        _owner_error(handler, exc)
        return True
    private_link = "/review-d132.html#token=" + quote(issued.token, safe="")
    handler._json(
        {
            "round_id": issued.principal.round_id,
            "reviewer_id": issued.reviewer.id,
            "expires_at": issued.principal.expires_at.isoformat(),
            "private_link": private_link,
            "token_returned_once": True,
            "token_persisted_raw": False,
        },
        HTTPStatus.CREATED,
    )
    return True


def _guest_decision(handler: NutEVHandler) -> bool:
    if not _pilot_enabled(handler):
        return True
    token = _guest_token(handler)
    if not token:
        handler._json({"error": "review_token_required"}, HTTPStatus.UNAUTHORIZED)
        return True
    try:
        _require_guest_source_owner(token)
        body = handler._read_json()
        payload = _service().save_guest_decision(
            token,
            assignment_id=str(body.get("assignment_id") or "").strip(),
            decision_value=str(body.get("decision_value") or "").strip(),
            reason=str(body.get("reason") or "").strip(),
            notes=str(body.get("notes") or "").strip(),
        )
    except Exception as exc:
        _guest_error(handler, exc)
        return True
    handler._json(payload)
    return True


def _guest_submit(handler: NutEVHandler) -> bool:
    if not _pilot_enabled(handler):
        return True
    token = _guest_token(handler)
    if not token:
        handler._json({"error": "review_token_required"}, HTTPStatus.UNAUTHORIZED)
        return True
    try:
        _require_guest_source_owner(token)
        payload = _service().submit_guest(token)
    except Exception as exc:
        _guest_error(handler, exc)
        return True
    handler._json(payload)
    return True


def _owner_adjudication(handler: NutEVHandler, *, finalize: bool) -> bool:
    resolved = _article1_project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        body = handler._read_json()
        round_id = str(body.get("round_id") or "").strip()
        if finalize:
            payload = _service().finalize_adjudication(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                project_access_confirmed=True,
                round_id=round_id,
            )
        else:
            payload = _service().save_adjudication(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                project_access_confirmed=True,
                round_id=round_id,
                item_key=str(body.get("item_key") or "").strip(),
                decision_value=str(body.get("decision_value") or "").strip(),
                notes=str(body.get("notes") or "").strip(),
            )
    except Exception as exc:
        _owner_error(handler, exc)
        return True
    handler._json(payload)
    return True


def _article1_post(handler: NutEVHandler, parsed) -> bool:
    routes = {
        "/api/article1/d132/rounds": _create_round,
        "/api/article1/d132/guest": _issue_guest,
        "/api/article1/d132/decision": _guest_decision,
        "/api/article1/d132/submit": _guest_submit,
    }
    action = routes.get(parsed.path)
    if action is not None:
        return action(handler)
    if parsed.path == "/api/article1/d132/adjudication":
        return _owner_adjudication(handler, finalize=False)
    if parsed.path == "/api/article1/d132/finalize":
        return _owner_adjudication(handler, finalize=True)
    return False


def install_article1_d132_routes() -> None:
    """Install the Article 1 assembly on the shared handler exactly once."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_get = NutEVHandler.do_GET
    original_post = NutEVHandler.do_POST

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _article1_get(self, parsed):
            return
        original_get(self)

    def do_post(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _article1_post(self, parsed):
            return
        original_post(self)

    NutEVHandler.do_GET = do_get
    NutEVHandler.do_POST = do_post
