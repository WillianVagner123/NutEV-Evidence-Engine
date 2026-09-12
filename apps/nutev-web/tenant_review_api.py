from __future__ import annotations

from http import HTTPStatus
import os
from pathlib import Path
import threading
from urllib.parse import unquote, urlparse

from nutev.review import HumanReviewEngine, ReviewPolicy, SQLiteHumanReviewStore
from nutev.review.application_scope import (
    ApplicationScopedReviewService,
    SQLiteReviewApplicationBindingStore,
)
from nutev.tenancy import (
    ApplicationService,
    SQLiteApplicationStore,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
)
from server import APP_ROOT, NutEVHandler

_SERVICE_LOCK = threading.Lock()
_SERVICE: ApplicationScopedReviewService | None = None
_INSTALLED = False


def _platform_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "auth.sqlite3").resolve()


def _service() -> ApplicationScopedReviewService:
    global _SERVICE
    with _SERVICE_LOCK:
        if _SERVICE is None:
            database = _platform_database()
            access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
            applications = ApplicationService(SQLiteApplicationStore(database), access)
            engine = HumanReviewEngine(SQLiteHumanReviewStore(database))
            bindings = SQLiteReviewApplicationBindingStore(database)
            _SERVICE = ApplicationScopedReviewService(engine, applications, bindings)
        return _SERVICE


def _project_context(handler: NutEVHandler):
    enabled = getattr(handler, "_auth_pilot_enabled", None)
    if not callable(enabled) or not enabled():
        handler._json({"error": "auth_pilot_disabled"}, HTTPStatus.NOT_FOUND)
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


def _error(handler: NutEVHandler, exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        handler._json({"error": "review_access_denied"}, HTTPStatus.FORBIDDEN)
    elif isinstance(exc, FileNotFoundError):
        handler._json({"error": "review_round_not_found"}, HTTPStatus.NOT_FOUND)
    elif isinstance(exc, KeyError):
        handler._json({"error": "review_context_not_found"}, HTTPStatus.NOT_FOUND)
    elif isinstance(exc, LookupError):
        handler._json({"error": str(exc) or "review_application_required"}, HTTPStatus.CONFLICT)
    elif isinstance(exc, ValueError):
        handler._json({"error": "invalid_review_request", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
    else:
        raise exc


def _overview(handler: NutEVHandler) -> bool:
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        payload = _service().overview(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except Exception as exc:
        _error(handler, exc)
        return True
    handler._json(payload)
    return True


def _round_get(handler: NutEVHandler, path: str) -> bool:
    prefix = "/api/review/rounds/"
    if not path.startswith(prefix):
        return False
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    tail = unquote(path[len(prefix) :]).strip("/")
    assignments = False
    if tail.endswith("/assignments"):
        tail = tail[: -len("/assignments")].strip("/")
        assignments = True
    if not tail or "/" in tail:
        handler._json({"error": "review_round_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    try:
        if assignments:
            payload = _service().reviewer_payload(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                round_id=tail,
            )
        else:
            payload = _service().round_summary(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                round_id=tail,
            )
    except Exception as exc:
        _error(handler, exc)
        return True
    handler._json(payload)
    return True


def _review_get(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/review":
        return _overview(handler)
    return _round_get(handler, parsed.path)


def _policy(body: dict) -> ReviewPolicy:
    raw_options = body.get("decision_options")
    if raw_options is None:
        options = ("include", "exclude", "uncertain")
    elif isinstance(raw_options, list):
        options = tuple(str(item).strip() for item in raw_options if str(item).strip())
    else:
        raise ValueError("decision_options must be an array")
    if not options:
        raise ValueError("at least one decision option is required")
    if len(options) > 20 or any(len(item) > 80 for item in options):
        raise ValueError("decision_options exceed the allowed size")
    minimum = int(body.get("minimum_reviewers_per_item") or 2)
    return ReviewPolicy(
        decision_options=options,
        reason_required=body.get("reason_required") is not False,
        minimum_reviewers_per_item=minimum,
    )


def _create_round(handler: NutEVHandler) -> bool:
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        body = handler._read_json()
        name = str(body.get("name") or "").strip()
        if not name:
            raise ValueError("review round name is required")
        if len(name) > 200:
            raise ValueError("review round name is too long")
        payload = _service().create_round(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            name=name,
            policy=_policy(body),
        )
    except Exception as exc:
        _error(handler, exc)
        return True
    handler._json(payload, HTTPStatus.CREATED)
    return True


def _save_decision(handler: NutEVHandler) -> bool:
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        body = handler._read_json()
        payload = _service().save_decision(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            round_id=str(body.get("round_id") or "").strip(),
            assignment_id=str(body.get("assignment_id") or "").strip(),
            decision_value=str(body.get("decision_value") or "").strip(),
            reason=str(body.get("reason") or "").strip(),
            notes=str(body.get("notes") or "").strip(),
        )
    except Exception as exc:
        _error(handler, exc)
        return True
    handler._json(payload)
    return True


def _submit(handler: NutEVHandler) -> bool:
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        body = handler._read_json()
        payload = _service().submit(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            round_id=str(body.get("round_id") or "").strip(),
        )
    except Exception as exc:
        _error(handler, exc)
        return True
    handler._json(payload)
    return True


def _review_post(handler: NutEVHandler, parsed) -> bool:
    routes = {
        "/api/review/rounds": _create_round,
        "/api/review/decision": _save_decision,
        "/api/review/submit": _submit,
    }
    action = routes.get(parsed.path)
    if action is None:
        return False
    return action(handler)


def install_review_routes() -> None:
    """Install generic authenticated Review routes exactly once."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_get = NutEVHandler.do_GET
    original_post = NutEVHandler.do_POST

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _review_get(self, parsed):
            return
        original_get(self)

    def do_post(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _review_post(self, parsed):
            return
        original_post(self)

    NutEVHandler.do_GET = do_get
    NutEVHandler.do_POST = do_post
