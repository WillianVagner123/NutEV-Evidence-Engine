from __future__ import annotations

from http import HTTPStatus
import os
from pathlib import Path
import threading
from urllib.parse import urlparse

from nutev.tenancy import (
    ApplicationService,
    SQLiteApplicationStore,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
)
from server import APP_ROOT, NutEVHandler

_SERVICE_LOCK = threading.Lock()
_SERVICE: ApplicationService | None = None
_INSTALLED = False


def _platform_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "auth.sqlite3").resolve()


def _service() -> ApplicationService:
    global _SERVICE
    with _SERVICE_LOCK:
        if _SERVICE is None:
            database = _platform_database()
            access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
            _SERVICE = ApplicationService(SQLiteApplicationStore(database), access)
        return _SERVICE


def _pilot_enabled(handler: NutEVHandler) -> bool:
    enabled = getattr(handler, "_auth_pilot_enabled", None)
    if not callable(enabled) or not enabled():
        handler._json({"error": "auth_pilot_disabled"}, HTTPStatus.NOT_FOUND)
        return False
    return True


def _authenticated_session(handler: NutEVHandler):
    if not _pilot_enabled(handler):
        return None
    resolver = getattr(handler, "_resolve_authenticated_session", None)
    if not callable(resolver):
        handler._json({"error": "authentication_required"}, HTTPStatus.UNAUTHORIZED)
        return None
    return resolver()


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


def _application_get(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/application/templates":
        session = _authenticated_session(handler)
        if session is None:
            return True
        templates = [template.descriptor() for template in _service().list_templates()]
        handler._json(
            {
                "templates": templates,
                "template_state_is_public_reusable": True,
                "project_configuration_is_private": True,
                "closed_application_type_enum": False,
            }
        )
        return True

    if parsed.path != "/api/application":
        return False
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        instance = _service().get(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except (KeyError, PermissionError, ValueError):
        handler._json({"error": "application_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    handler._json(
        {
            "workspace_id": workspace_id,
            "project_id": project_id,
            "application": instance.descriptor() if instance else None,
        }
    )
    return True


def _application_post(handler: NutEVHandler, parsed) -> bool:
    if parsed.path != "/api/application":
        return False
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        payload = handler._read_json()
        configuration = payload.get("configuration")
        if configuration is None:
            configuration = {}
        if not isinstance(configuration, dict):
            raise ValueError("configuration must be an object")
        instance = _service().configure(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            application_type=str(payload.get("application_type") or "") or None,
            template_id=str(payload.get("template_id") or "") or None,
            template_version=str(payload.get("template_version") or "") or None,
            config_version=str(payload.get("config_version") or "1"),
            configuration=configuration,
        )
    except KeyError as exc:
        if str(exc).strip("'") == "application_template_not_found":
            handler._json({"error": "application_template_not_found"}, HTTPStatus.NOT_FOUND)
        else:
            handler._json({"error": "application_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    except PermissionError:
        handler._json({"error": "application_access_denied"}, HTTPStatus.FORBIDDEN)
        return True
    except ValueError as exc:
        handler._json({"error": "invalid_application", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        return True
    handler._json(
        {
            "workspace_id": workspace_id,
            "project_id": project_id,
            "application": instance.descriptor(),
        },
        HTTPStatus.CREATED,
    )
    return True


def install_application_routes() -> None:
    """Install project-application routes on the shared handler exactly once."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_get = NutEVHandler.do_GET
    original_post = NutEVHandler.do_POST

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _application_get(self, parsed):
            return
        original_get(self)

    def do_post(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _application_post(self, parsed):
            return
        original_post(self)

    NutEVHandler.do_GET = do_get
    NutEVHandler.do_POST = do_post
