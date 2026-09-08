from __future__ import annotations

from http import HTTPStatus
from urllib.parse import urlparse

from nutev.tenancy import SCOPING_REVIEW
from server import NutEVHandler
from tenant_application_api import _service as application_service

_INSTALLED = False
_A1_ASSEMBLY_ID = "WILLIAN_DOCTORATE_A1"


def _pilot_enabled(handler: NutEVHandler) -> bool:
    enabled = getattr(handler, "_auth_pilot_enabled", None)
    return bool(callable(enabled) and enabled())


def _project_context(handler: NutEVHandler):
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


def _article1_context_allowed(handler: NutEVHandler) -> bool:
    resolved = _project_context(handler)
    if resolved is None:
        return False
    principal, workspace_id, project_id = resolved
    try:
        application = application_service().get(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
        )
    except (KeyError, PermissionError, ValueError):
        handler._json({"error": "article1_context_not_found"}, HTTPStatus.NOT_FOUND)
        return False
    if application is None:
        handler._json({"error": "article1_context_not_found"}, HTTPStatus.NOT_FOUND)
        return False
    descriptor = application.descriptor()
    configuration = descriptor.get("configuration")
    if (
        descriptor.get("template_id") != SCOPING_REVIEW
        or not isinstance(configuration, dict)
        or configuration.get("assembly_id") != _A1_ASSEMBLY_ID
    ):
        handler._json({"error": "article1_context_not_found"}, HTTPStatus.NOT_FOUND)
        return False
    return True


def _release_guard_get(handler: NutEVHandler, path: str) -> bool:
    if not _pilot_enabled(handler):
        return False

    # The legacy Workbench mixes global bibliographic identity with scientific
    # projection state. Until it has a tenant-safe projection, pilot mode must not
    # expose it through the old /api/articles surface.
    if path == "/api/articles" or path.startswith("/api/articles/"):
        if _project_context(handler) is None:
            return True
        handler._json(
            {
                "error": "legacy_workbench_unavailable_in_pilot",
                "replacement": "/api/library",
                "semantics": "fail-closed: use tenant-scoped Evidence Library in authenticated mode",
            },
            HTTPStatus.NOT_FOUND,
        )
        return True

    # Article 1 static context is scientific-private material. Caddy remains an
    # outer perimeter, but pilot mode additionally requires the selected project
    # to be the Article 1 SCOPING_REVIEW application.
    if path.startswith("/agent-context/article1/"):
        return not _article1_context_allowed(handler)

    return False


def install_tenant_release_guard() -> None:
    """Install final pilot-mode privacy guards on the shared base handler."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_get = NutEVHandler.do_GET

    def do_get(self: NutEVHandler) -> None:
        path = urlparse(self.path).path
        if _release_guard_get(self, path):
            return
        original_get(self)

    NutEVHandler.do_GET = do_get
