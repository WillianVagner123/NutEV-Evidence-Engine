from __future__ import annotations

from http import HTTPStatus
import threading
from urllib.parse import urlparse

from nutev.applications.willian_doctorate_a2 import A2ConfigurationError, A2IntegrativeService
from nutev.tenancy import INTEGRATIVE_REVIEW
from server import APP_ROOT, NutEVHandler
from tenant_application_api import _platform_database, _project_context, _service as application_service

_SERVICE_LOCK = threading.Lock()
_SERVICE: A2IntegrativeService | None = None
_INSTALLED = False
ASSEMBLY_ID = "WILLIAN_DOCTORATE_A2"


def _service() -> A2IntegrativeService:
    global _SERVICE
    with _SERVICE_LOCK:
        if _SERVICE is None:
            _SERVICE = A2IntegrativeService(
                repo_root=APP_ROOT.parents[1],
                database_path=_platform_database(),
            )
        return _SERVICE


def _article2_context(handler: NutEVHandler):
    resolved = _project_context(handler)
    if resolved is None:
        return None
    principal, workspace_id, project_id = resolved
    try:
        application = application_service().get(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except (KeyError, PermissionError, ValueError):
        handler._json({"error": "article2_project_not_found"}, HTTPStatus.NOT_FOUND)
        return None
    if application is None:
        handler._json({"error": "article2_application_required"}, HTTPStatus.CONFLICT)
        return None
    descriptor = application.descriptor()
    configuration = descriptor.get("configuration")
    if not isinstance(configuration, dict):
        handler._json({"error": "article2_application_required"}, HTTPStatus.CONFLICT)
        return None
    if descriptor.get("template_id") != INTEGRATIVE_REVIEW:
        handler._json({"error": "article2_application_required"}, HTTPStatus.CONFLICT)
        return None
    if configuration.get("assembly_id") != ASSEMBLY_ID:
        handler._json({"error": "article2_application_required"}, HTTPStatus.NOT_FOUND)
        return None
    if configuration.get("integrative_config_version") != _service().config().config_version:
        handler._json({"error": "article2_integrative_config_mismatch"}, HTTPStatus.CONFLICT)
        return None
    application_id = str(descriptor.get("id") or "").strip()
    if not application_id:
        handler._json({"error": "article2_application_required"}, HTTPStatus.CONFLICT)
        return None
    return principal, workspace_id, project_id, application_id


def _error(handler: NutEVHandler, exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        handler._json({"error": "article2_integrative_access_denied"}, HTTPStatus.FORBIDDEN)
    elif isinstance(exc, FileNotFoundError):
        handler._json({"error": "article2_integrative_not_found"}, HTTPStatus.NOT_FOUND)
    elif isinstance(exc, A2ConfigurationError):
        handler._json({"error": "article2_integrative_config_invalid", "message": str(exc)}, HTTPStatus.CONFLICT)
    elif isinstance(exc, ValueError):
        message = str(exc)
        status = HTTPStatus.CONFLICT if "LEGACY_BINDING_REQUIRED" in message or "not active" in message else HTTPStatus.BAD_REQUEST
        handler._json({"error": "article2_integrative_blocked", "message": message}, status)
    else:
        raise exc


def _status(handler: NutEVHandler, *, events: bool = False) -> bool:
    resolved = _article2_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id, application_id = resolved
    try:
        if events:
            payload = {
                "events": list(
                    _service().events(
                        principal,
                        workspace_id=workspace_id,
                        project_id=project_id,
                        application_id=application_id,
                        project_access_confirmed=True,
                    )
                )
            }
        else:
            payload = _service().status(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                application_id=application_id,
                project_access_confirmed=True,
            )
    except Exception as exc:
        _error(handler, exc)
        return True
    handler._json(payload)
    return True


def _bootstrap(handler: NutEVHandler) -> bool:
    resolved = _article2_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id, application_id = resolved
    try:
        state = _service().bootstrap(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            project_access_confirmed=True,
        )
        payload = _service().status(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            project_access_confirmed=True,
        )
    except Exception as exc:
        _error(handler, exc)
        return True
    handler._json({"workflow_id": state.workflow_id, **payload}, HTTPStatus.CREATED)
    return True


def _advance(handler: NutEVHandler) -> bool:
    resolved = _article2_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id, application_id = resolved
    try:
        body = handler._read_json()
        _service().advance(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            project_access_confirmed=True,
            next_phase=str(body.get("next_phase") or "").strip(),
            evidence=str(body.get("evidence") or "").strip(),
        )
        payload = _service().status(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            application_id=application_id,
            project_access_confirmed=True,
        )
    except Exception as exc:
        _error(handler, exc)
        return True
    handler._json(payload)
    return True


def _article2_get(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/article2/integrative/status":
        return _status(handler)
    if parsed.path == "/api/article2/integrative/events":
        return _status(handler, events=True)
    return False


def _article2_post(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/article2/integrative/bootstrap":
        return _bootstrap(handler)
    if parsed.path == "/api/article2/integrative/advance":
        return _advance(handler)
    return False


def install_article2_integrative_routes() -> None:
    """Install Article 2 application routes without exposing legacy-binding activation."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_get = NutEVHandler.do_GET
    original_post = NutEVHandler.do_POST

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _article2_get(self, parsed):
            return
        original_get(self)

    def do_post(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _article2_post(self, parsed):
            return
        original_post(self)

    NutEVHandler.do_GET = do_get
    NutEVHandler.do_POST = do_post
