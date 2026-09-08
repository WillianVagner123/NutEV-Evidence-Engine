from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
import os
from pathlib import Path
import threading
from urllib.parse import parse_qs, unquote, urlparse

from nutev.tenancy import (
    EvidenceLibraryEntry,
    EvidenceLibraryService,
    GlobalEvidenceRegistryReader,
    SQLiteEvidenceLibraryStore,
    SQLiteWorkspaceProjectStore,
    WorkspaceProjectService,
)
from server import APP_ROOT, NutEVHandler

_SERVICE_LOCK = threading.Lock()
_SERVICE: EvidenceLibraryService | None = None
_INSTALLED = False


def _platform_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "auth.sqlite3").resolve()


def _registry_database() -> Path:
    configured = str(os.environ.get("NUTEV_REGISTRY_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "registry" / "article_registry.sqlite").resolve()


def _service() -> EvidenceLibraryService:
    global _SERVICE
    with _SERVICE_LOCK:
        if _SERVICE is None:
            platform = _platform_database()
            workspace = WorkspaceProjectService(SQLiteWorkspaceProjectStore(platform))
            _SERVICE = EvidenceLibraryService(
                SQLiteEvidenceLibraryStore(platform),
                GlobalEvidenceRegistryReader(_registry_database()),
                workspace,
            )
        return _SERVICE


def _entry_payload(entry: EvidenceLibraryEntry) -> dict[str, object]:
    placement = entry.placement
    document = entry.document
    return {
        "placement": {
            "placement_id": placement.placement_id,
            "workspace_id": placement.workspace_id,
            "project_id": placement.project_id,
            "article_id": placement.article_id,
            "state": placement.state,
            "tags": list(placement.tags),
            "notes": placement.notes,
            "created_at": placement.created_at.isoformat(),
            "updated_at": placement.updated_at.isoformat(),
        },
        "document": {
            "article_id": document.article_id,
            "title": document.title,
            "year": document.year,
            "journal": document.journal,
            "abstract": document.abstract,
            "doi": document.doi,
            "pmid": document.pmid,
            "pmcid": document.pmcid,
        },
    }


def _secure_context(handler: NutEVHandler):
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
    return session.principal, snapshot.current


def _library_get(handler: NutEVHandler, parsed) -> bool:
    path = parsed.path
    if path == "/api/library":
        resolved = _secure_context(handler)
        if resolved is None:
            return True
        principal, current = resolved
        query = parse_qs(parsed.query)
        scope = str((query.get("scope") or ["workspace"])[0]).strip().casefold()
        try:
            limit = max(1, min(int((query.get("limit") or ["200"])[0]), 500))
        except ValueError:
            limit = 200
        try:
            entries = _service().list(principal, current, scope=scope, limit=limit)
        except PermissionError as exc:
            code = str(exc) or "evidence_library_denied"
            status = HTTPStatus.CONFLICT if "context_required" in code else HTTPStatus.FORBIDDEN
            handler._json({"error": code}, status)
            return True
        except ValueError:
            handler._json({"error": "invalid_library_scope"}, HTTPStatus.BAD_REQUEST)
            return True
        except FileNotFoundError:
            handler._json(
                {
                    "error": "global_registry_not_ready",
                    "message": "The canonical Article Registry is not materialized in this runtime.",
                },
                HTTPStatus.CONFLICT,
            )
            return True
        handler._json(
            {
                "scope": scope,
                "workspace_id": current.workspace_id,
                "project_id": current.project_id if scope == "project" else None,
                "entries": [_entry_payload(entry) for entry in entries],
                "global_document_metadata_shared": True,
                "placement_state_private": True,
            }
        )
        return True

    if path.startswith("/api/library/placements/"):
        resolved = _secure_context(handler)
        if resolved is None:
            return True
        principal, current = resolved
        placement_id = unquote(path[len("/api/library/placements/"):]).strip()
        try:
            entry = _service().require_placement(principal, current, placement_id)
        except (KeyError, PermissionError, ValueError):
            handler._json({"error": "placement_not_found"}, HTTPStatus.NOT_FOUND)
            return True
        except FileNotFoundError:
            handler._json({"error": "global_registry_not_ready"}, HTTPStatus.CONFLICT)
            return True
        handler._json(_entry_payload(entry))
        return True

    if path.startswith("/api/library/full-text/"):
        resolved = _secure_context(handler)
        if resolved is None:
            return True
        principal, current = resolved
        article_id = unquote(path[len("/api/library/full-text/"):]).strip()
        try:
            grants = _service().full_text_access(principal, current, article_id)
        except (KeyError, PermissionError, ValueError):
            handler._json({"error": "full_text_access_not_found"}, HTTPStatus.NOT_FOUND)
            return True
        except FileNotFoundError:
            handler._json({"error": "global_registry_not_ready"}, HTTPStatus.CONFLICT)
            return True
        handler._json(
            {
                "article_id": article_id,
                "workspace_id": current.workspace_id,
                "project_id": current.project_id,
                "grants": [grant.public_descriptor() for grant in grants],
                "cache_path_exposed": False,
            }
        )
        return True

    return False


def _library_post(handler: NutEVHandler, parsed) -> bool:
    if parsed.path != "/api/library/placements":
        return False
    resolved = _secure_context(handler)
    if resolved is None:
        return True
    principal, current = resolved
    try:
        payload = handler._read_json()
        article_id = str(payload.get("article_id") or "").strip()
        if not article_id:
            raise ValueError("article_id is required")
        raw_tags = payload.get("tags")
        tags = [str(item) for item in raw_tags] if isinstance(raw_tags, list) else []
        entry = _service().save(
            principal,
            current,
            article_id=article_id,
            scope=str(payload.get("scope") or "workspace"),
            state=str(payload.get("state") or "not_screened"),
            tags=tags,
            notes=str(payload.get("notes") or ""),
        )
    except KeyError:
        handler._json({"error": "global_document_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    except PermissionError as exc:
        code = str(exc) or "evidence_library_denied"
        status = HTTPStatus.CONFLICT if "context_required" in code else HTTPStatus.FORBIDDEN
        handler._json({"error": code}, status)
        return True
    except ValueError as exc:
        handler._json({"error": "invalid_placement", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        return True
    except FileNotFoundError:
        handler._json({"error": "global_registry_not_ready"}, HTTPStatus.CONFLICT)
        return True
    handler._json(_entry_payload(entry), HTTPStatus.CREATED)
    return True


def _library_delete(handler: NutEVHandler, parsed) -> bool:
    path = parsed.path
    if not path.startswith("/api/library/placements/"):
        return False
    resolved = _secure_context(handler)
    if resolved is None:
        return True
    principal, current = resolved
    placement_id = unquote(path[len("/api/library/placements/"):]).strip()
    try:
        deleted = _service().delete(principal, current, placement_id)
    except (KeyError, PermissionError, ValueError):
        handler._json({"error": "placement_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    handler._json({"deleted": bool(deleted), "placement_id": placement_id})
    return True


def install_library_routes() -> None:
    """Install authenticated library routes on the base handler exactly once.

    SecureNutEVHandler calls ``super()`` for unknown paths, so these routes inherit the
    already-resolved authentication/context boundary without modifying scientific handlers.
    """
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_get = NutEVHandler.do_GET
    original_post = NutEVHandler.do_POST
    original_delete = getattr(NutEVHandler, "do_DELETE", None)

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _library_get(self, parsed):
            return
        original_get(self)

    def do_post(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _library_post(self, parsed):
            return
        original_post(self)

    def do_delete(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _library_delete(self, parsed):
            return
        if original_delete is not None:
            original_delete(self)
            return
        self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    NutEVHandler.do_GET = do_get
    NutEVHandler.do_POST = do_post
    NutEVHandler.do_DELETE = do_delete
