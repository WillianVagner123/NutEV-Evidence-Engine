from __future__ import annotations

from collections import defaultdict, deque
from http import HTTPStatus
import os
from pathlib import Path
import re
import threading
import time
from urllib.parse import parse_qs, quote, urlparse

from nutev.tenancy.access_requests import SQLiteAccessRequestStore
from nutev.tenancy.models import GlobalRole
from nutev.tenancy.password_reset import SQLitePasswordResetStore
from transactional_email import public_origin, send_access_approved_email, send_password_reset_email
from server import APP_ROOT, NutEVHandler

_SERVICE_LOCK = threading.Lock()
_SERVICE: SQLiteAccessRequestStore | None = None
_RESET_SERVICE: SQLitePasswordResetStore | None = None
_RATE_LOCK = threading.Lock()
_ACCESS_REQUEST_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
_INVITATION_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
_PASSWORD_RESET_REQUEST_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
_PASSWORD_RESET_CONFIRM_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
_RATE_WINDOW_SECONDS = 10 * 60
_ACCESS_REQUEST_IP_LIMIT = 5
_INVITATION_IP_LIMIT = 20
_PASSWORD_RESET_REQUEST_IP_LIMIT = 5
_PASSWORD_RESET_CONFIRM_IP_LIMIT = 20
_ADMIN_PATH_RE = re.compile(r"^/api/admin/access-requests/(?P<request_id>acr_[a-f0-9]{32})/(?P<action>approve|reject)$")
_INSTALLED = False


def _platform_database() -> Path:
    configured = str(os.environ.get("NUTEV_AUTH_DB") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (APP_ROOT.parents[1] / "project_output_reference" / "platform" / "auth.sqlite3").resolve()


def _service() -> SQLiteAccessRequestStore:
    global _SERVICE
    with _SERVICE_LOCK:
        if _SERVICE is None:
            _SERVICE = SQLiteAccessRequestStore(_platform_database())
        return _SERVICE


def _reset_service() -> SQLitePasswordResetStore:
    global _RESET_SERVICE
    with _SERVICE_LOCK:
        if _RESET_SERVICE is None:
            _RESET_SERVICE = SQLitePasswordResetStore(_platform_database())
        return _RESET_SERVICE


def _client_ip(handler: NutEVHandler) -> str:
    forwarded = str(handler.headers.get("X-Forwarded-For") or "").split(",", 1)[0].strip()
    if forwarded:
        return forwarded
    address = getattr(handler, "client_address", ("unknown", 0))
    return str(address[0])


def _consume(bucket: dict[str, deque[float]], key: str, limit: int) -> bool:
    now = time.monotonic()
    with _RATE_LOCK:
        values = bucket[key]
        while values and now - values[0] > _RATE_WINDOW_SECONDS:
            values.popleft()
        if len(values) >= limit:
            return False
        values.append(now)
        return True


def _pilot_enabled(handler: NutEVHandler) -> bool:
    enabled = getattr(handler, "_auth_pilot_enabled", None)
    if not callable(enabled) or not enabled():
        handler._json({"error": "auth_pilot_disabled"}, HTTPStatus.NOT_FOUND)
        return False
    return True


def _platform_admin(handler: NutEVHandler):
    if not _pilot_enabled(handler):
        return None
    resolver = getattr(handler, "_resolve_authenticated_session", None)
    if not callable(resolver):
        handler._json({"error": "authentication_required"}, HTTPStatus.UNAUTHORIZED)
        return None
    session = resolver()
    if session is None:
        return None
    if GlobalRole.PLATFORM_ADMIN not in session.principal.global_roles:
        handler._json({"error": "platform_admin_required"}, HTTPStatus.FORBIDDEN)
        return None
    return session


def _submit_access_request(handler: NutEVHandler) -> bool:
    if not _pilot_enabled(handler):
        return True
    if not _consume(_ACCESS_REQUEST_ATTEMPTS, _client_ip(handler), _ACCESS_REQUEST_IP_LIMIT):
        handler._json({"error": "access_request_rate_limited"}, HTTPStatus.TOO_MANY_REQUESTS)
        return True
    try:
        payload = handler._read_json()
    except ValueError:
        handler._json({"error": "invalid_access_request"}, HTTPStatus.BAD_REQUEST)
        return True
    if str(payload.get("website") or "").strip():
        handler._json({"status": "received"}, HTTPStatus.ACCEPTED)
        return True
    try:
        _service().submit(
            email=str(payload.get("email") or ""),
            display_name=str(payload.get("display_name") or ""),
            institution=str(payload.get("institution") or ""),
            intended_use=str(payload.get("intended_use") or ""),
        )
    except ValueError as exc:
        handler._json({"error": "invalid_access_request", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        return True
    except Exception:
        handler._json({"error": "access_request_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True
    handler._json({"status": "received", "message": "Sua solicitação foi recebida para análise."}, HTTPStatus.ACCEPTED)
    return True


def _invitation_status(handler: NutEVHandler, parsed) -> bool:
    if not _pilot_enabled(handler):
        return True
    token = str((parse_qs(parsed.query).get("token") or [""])[0]).strip()
    try:
        request = _service().inspect_invitation(token)
    except Exception:
        handler._json({"error": "access_request_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True
    if request is None:
        handler._json({"valid": False}, HTTPStatus.OK)
        return True
    handler._json({
        "valid": True,
        "display_name": request.display_name,
        "email": request.email,
        "expires_at": request.invitation_expires_at.isoformat() if request.invitation_expires_at else None,
    }, HTTPStatus.OK)
    return True


def _accept_invitation(handler: NutEVHandler) -> bool:
    if not _pilot_enabled(handler):
        return True
    if not _consume(_INVITATION_ATTEMPTS, _client_ip(handler), _INVITATION_IP_LIMIT):
        handler._json({"error": "invitation_rate_limited"}, HTTPStatus.TOO_MANY_REQUESTS)
        return True
    try:
        payload = handler._read_json()
        token = str(payload.get("token") or "").strip()
        password = str(payload.get("password") or "")
        user = _service().accept_invitation(token, password=password)
    except KeyError:
        handler._json({"error": "invalid_or_expired_invitation"}, HTTPStatus.BAD_REQUEST)
        return True
    except ValueError as exc:
        message = str(exc)
        code = "account_already_exists" if "already exists" in message else "invalid_password"
        handler._json({"error": code, "message": message}, HTTPStatus.BAD_REQUEST)
        return True
    except Exception:
        handler._json({"error": "access_request_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True
    handler._json({"status": "account_created", "email": user.email, "display_name": user.display_name, "login_path": "/login.html"}, HTTPStatus.CREATED)
    return True


def _password_reset_request(handler: NutEVHandler) -> bool:
    if not _pilot_enabled(handler):
        return True
    if not _consume(_PASSWORD_RESET_REQUEST_ATTEMPTS, _client_ip(handler), _PASSWORD_RESET_REQUEST_IP_LIMIT):
        handler._json({"error": "password_reset_rate_limited"}, HTTPStatus.TOO_MANY_REQUESTS)
        return True
    try:
        payload = handler._read_json()
        email = str(payload.get("email") or "")
        ticket = _reset_service().issue(email)
        if ticket is not None:
            origin = public_origin()
            if origin:
                path = f"/reset-password.html?token={quote(ticket.token, safe='')}"
                send_password_reset_email(
                    recipient=ticket.reset.email,
                    display_name=ticket.reset.display_name,
                    reset_url=origin + path,
                )
    except Exception:
        # The public response remains deliberately generic to avoid account enumeration.
        pass
    handler._json({
        "status": "received",
        "message": "Se existir uma conta ativa para este e-mail, enviaremos as instruções de redefinição.",
    }, HTTPStatus.ACCEPTED)
    return True


def _password_reset_status(handler: NutEVHandler, parsed) -> bool:
    if not _pilot_enabled(handler):
        return True
    token = str((parse_qs(parsed.query).get("token") or [""])[0]).strip()
    try:
        reset = _reset_service().inspect(token)
    except Exception:
        handler._json({"error": "password_reset_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True
    if reset is None:
        handler._json({"valid": False}, HTTPStatus.OK)
        return True
    handler._json({
        "valid": True,
        "display_name": reset.display_name,
        "email": reset.email,
        "expires_at": reset.expires_at.isoformat(),
    }, HTTPStatus.OK)
    return True


def _password_reset_confirm(handler: NutEVHandler) -> bool:
    if not _pilot_enabled(handler):
        return True
    if not _consume(_PASSWORD_RESET_CONFIRM_ATTEMPTS, _client_ip(handler), _PASSWORD_RESET_CONFIRM_IP_LIMIT):
        handler._json({"error": "password_reset_rate_limited"}, HTTPStatus.TOO_MANY_REQUESTS)
        return True
    try:
        payload = handler._read_json()
        user = _reset_service().consume(
            str(payload.get("token") or ""),
            password=str(payload.get("password") or ""),
        )
    except KeyError:
        handler._json({"error": "invalid_or_expired_password_reset"}, HTTPStatus.BAD_REQUEST)
        return True
    except ValueError as exc:
        handler._json({"error": "invalid_password", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        return True
    except Exception:
        handler._json({"error": "password_reset_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True
    handler._json({"status": "password_updated", "email": user.email, "login_path": "/login.html"}, HTTPStatus.OK)
    return True


def _admin_list(handler: NutEVHandler, parsed) -> bool:
    session = _platform_admin(handler)
    if session is None:
        return True
    status = str((parse_qs(parsed.query).get("status") or ["pending"])[0]).strip().casefold()
    try:
        requests = _service().list(status=status)
    except ValueError as exc:
        handler._json({"error": "invalid_access_request_status", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        return True
    except Exception:
        handler._json({"error": "access_request_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True
    handler._json({"requests": [item.admin_payload() for item in requests], "status": status, "administrator": session.user.display_name})
    return True


def _admin_decision(handler: NutEVHandler, match: re.Match[str]) -> bool:
    session = _platform_admin(handler)
    if session is None:
        return True
    request_id = match.group("request_id")
    action = match.group("action")
    try:
        if action == "approve":
            invitation = _service().approve(request_id, decided_by=session.principal.user_id)
            invitation_path = f"/set-password.html?token={quote(invitation.token, safe='')}"
            origin = public_origin()
            delivery = send_access_approved_email(
                recipient=invitation.request.email,
                display_name=invitation.request.display_name,
                invitation_url=(origin + invitation_path) if origin else "",
            )
            handler._json({
                "status": "approved",
                "request": invitation.request.admin_payload(),
                "invitation_path": invitation_path,
                "invitation_is_single_display": True,
                "email_delivery": delivery.status,
            }, HTTPStatus.OK)
            return True
        payload = handler._read_json()
        request = _service().reject(request_id, decided_by=session.principal.user_id, reason=str(payload.get("reason") or ""))
        handler._json({"status": "rejected", "request": request.admin_payload()}, HTTPStatus.OK)
        return True
    except KeyError:
        handler._json({"error": "access_request_not_found"}, HTTPStatus.NOT_FOUND)
        return True
    except ValueError as exc:
        handler._json({"error": "access_request_decision_denied", "message": str(exc)}, HTTPStatus.CONFLICT)
        return True
    except Exception:
        handler._json({"error": "access_request_service_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
        return True


def _access_get(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/access-invitations/status":
        return _invitation_status(handler, parsed)
    if parsed.path == "/api/auth/password-reset/status":
        return _password_reset_status(handler, parsed)
    if parsed.path == "/api/admin/access-requests":
        return _admin_list(handler, parsed)
    return False


def _access_post(handler: NutEVHandler, parsed) -> bool:
    if parsed.path == "/api/access-requests":
        return _submit_access_request(handler)
    if parsed.path == "/api/access-invitations/accept":
        return _accept_invitation(handler)
    if parsed.path == "/api/auth/password-reset/request":
        return _password_reset_request(handler)
    if parsed.path == "/api/auth/password-reset/confirm":
        return _password_reset_confirm(handler)
    match = _ADMIN_PATH_RE.fullmatch(parsed.path)
    if match:
        return _admin_decision(handler, match)
    return False


def install_access_request_routes() -> None:
    """Install governed access and recovery routes without touching scientific state."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    original_get = NutEVHandler.do_GET
    original_post = NutEVHandler.do_POST

    def do_get(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _access_get(self, parsed):
            return
        original_get(self)

    def do_post(self: NutEVHandler) -> None:
        parsed = urlparse(self.path)
        if _access_post(self, parsed):
            return
        original_post(self)

    NutEVHandler.do_GET = do_get
    NutEVHandler.do_POST = do_post
