from __future__ import annotations

from http import HTTPStatus
import os
from pathlib import Path
import re
import threading
from urllib.parse import parse_qs, unquote, urlparse

from nutev.tenancy import (
    ExportArtifactInput,
    ExportAuditError,
    ProjectExportAuditService,
    SQLiteApplicationStore,
    SQLiteProjectExportAuditStore,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
)
from server import APP_ROOT, NutEVHandler

_SERVICE_LOCK = threading.Lock()
_SERVICE: ProjectExportAuditService | None = None
_INSTALLED = False
_EXPORT_ID_RE = re.compile(r"^exp_[a-f0-9]{32}$")
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "workspace_id",
        "project_id",
        "application_id",
        "user_id",
        "created_by",
        "session_id",
        "search_id",
        "owner_scope",
    }
)


def _platform_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "auth.sqlite3").resolve()


def _export_root() -> Path:
    configured = str(os.environ.get("NUTEV_EXPORT_ROOT") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "exports").resolve()


def _service() -> ProjectExportAuditService:
    global _SERVICE
    with _SERVICE_LOCK:
        if _SERVICE is None:
            database = _platform_database()
            access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
            _SERVICE = ProjectExportAuditService(
                SQLiteProjectExportAuditStore(database),
                _export_root(),
                access,
                applications=SQLiteApplicationStore(database),
            )
        return _SERVICE


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


def _body_has_forbidden_identity(payload: dict) -> bool:
    return any(key in payload for key in _FORBIDDEN_BODY_KEYS)


def _parse_artifacts(payload: dict) -> tuple[ExportArtifactInput, ...]:
    raw = payload.get("artifacts")
    if not isinstance(raw, list) or not raw:
        raise ValueError("artifacts must be a non-empty array")
    artifacts: list[ExportArtifactInput] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"artifact {index} must be an object")
        if any(key in item for key in ("path", "file_path", "content_base64", "url")):
            raise ValueError("artifact source paths/base64/URLs are not accepted")
        content = item.get("content_text")
        if not isinstance(content, str):
            raise ValueError(f"artifact {index} content_text must be a string")
        artifacts.append(
            ExportArtifactInput(
                name=str(item.get("name") or ""),
                media_type=str(item.get("media_type") or "text/plain"),
                content=content.encode("utf-8"),
            )
        )
    return tuple(artifacts)


def _split_export_path(path: str):
    parts = [unquote(part) for part in path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "exports" and _EXPORT_ID_RE.fullmatch(parts[2]):
        return parts
    return None


def _send_artifact(handler: NutEVHandler, *, media_type: str, name: str, payload: bytes) -> None:
    safe_name = name.replace('"', "_").replace("\r", "_").replace("\n", "_")
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", f"{media_type}; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
    handler.send_header("Cache-Control", "private, no-store, max-age=0")
    handler.send_header("Pragma", "no-cache")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    handler.wfile.write(payload)


def _export_get(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/exports":
        resolved = _project_context(handler)
        if resolved is None:
            return True
        principal, workspace_id, project_id = resolved
        try:
            exports = _service().list_exports(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
            )
        except PermissionError:
            handler._json({"error": "export_audit_access_denied"}, HTTPStatus.FORBIDDEN)
            return True
        handler._json({"exports": [item.descriptor() for item in exports]})
        return True

    if parsed.path == "/api/audit":
        resolved = _project_context(handler)
        if resolved is None:
            return True
        principal, workspace_id, project_id = resolved
        query = parse_qs(parsed.query)
        try:
            limit = int((query.get("limit") or ["200"])[0])
            events = _service().audit_events(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                limit=limit,
            )
            chain_valid = _service().audit_chain_valid(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
            )
        except PermissionError:
            handler._json({"error": "export_audit_access_denied"}, HTTPStatus.FORBIDDEN)
            return True
        except ValueError as exc:
            handler._json({"error": "invalid_audit_request", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
            return True
        handler._json(
            {
                "workspace_id": workspace_id,
                "project_id": project_id,
                "chain_valid": chain_valid,
                "events": [event.descriptor() for event in events],
            }
        )
        return True

    parts = _split_export_path(parsed.path)
    if parts is None:
        return False
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    export_id = parts[2]
    try:
        if len(parts) == 4 and parts[3] == "manifest":
            manifest = _service().manifest(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                export_id=export_id,
            )
            handler._json({"manifest": manifest})
            return True
        if len(parts) == 5 and parts[3] == "artifacts":
            artifact, payload = _service().read_artifact(
                principal,
                workspace_id=workspace_id,
                project_id=project_id,
                export_id=export_id,
                name=parts[4],
            )
            _send_artifact(
                handler,
                media_type=artifact.media_type,
                name=artifact.name,
                payload=payload,
            )
            return True
    except (KeyError, FileNotFoundError, ValueError):
        handler._json({"error": "export_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    except PermissionError:
        handler._json({"error": "export_access_denied"}, HTTPStatus.FORBIDDEN)
        return True
    except ExportAuditError as exc:
        handler._json({"error": "export_integrity_error", "message": str(exc)}, HTTPStatus.CONFLICT)
        return True
    return False


def _export_post(handler: NutEVHandler, parsed) -> bool:
    if parsed.path != "/api/exports":
        return False
    resolved = _project_context(handler)
    if resolved is None:
        return True
    principal, workspace_id, project_id = resolved
    try:
        payload = handler._read_json()
        if not isinstance(payload, dict):
            raise ValueError("request body must be an object")
        if _body_has_forbidden_identity(payload):
            raise ValueError("tenant/project/application identity is session-derived")
        metadata = payload.get("metadata")
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        export = _service().create_export(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            export_kind=str(payload.get("export_kind") or ""),
            artifacts=_parse_artifacts(payload),
            metadata=metadata,
        )
        manifest = _service().manifest(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            export_id=export.id,
        )
    except PermissionError:
        handler._json({"error": "export_access_denied"}, HTTPStatus.FORBIDDEN)
        return True
    except ValueError as exc:
        handler._json({"error": "invalid_export", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        return True
    except ExportAuditError as exc:
        handler._json({"error": "export_integrity_error", "message": str(exc)}, HTTPStatus.CONFLICT)
        return True
    handler._json(
        {
            "workspace_id": workspace_id,
            "project_id": project_id,
            "export": export.descriptor(),
            "manifest": manifest,
        },
        HTTPStatus.CREATED,
    )
    return True


def install_export_audit_routes() -> None:
    """Install tenant export/audit routes on the shared handler exactly once."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_get = NutEVHandler.do_GET
    original_post = NutEVHandler.do_POST

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _export_get(self, parsed):
            return
        original_get(self)

    def do_post(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _export_post(self, parsed):
            return
        original_post(self)

    NutEVHandler.do_GET = do_get
    NutEVHandler.do_POST = do_post
