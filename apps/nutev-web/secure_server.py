from __future__ import annotations

from collections import defaultdict, deque
from hashlib import sha256
from http import HTTPStatus
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import re
import threading
import time
from urllib.parse import parse_qs, unquote, urlparse
from uuid import uuid4

from server import (
    APP_ROOT,
    NutEVHandler,
    _SEARCH_JOBS,
    _SEARCH_JOBS_LOCK,
    _create_search_job,
    _load_search_job,
)
from search_access import filter_owned_runs, record_search_owner, search_owned_by
from search_adapter import list_search_runs, load_search_run

SESSION_COOKIE = "nutev_session"
_SESSION_RE = re.compile(r"^[a-f0-9]{32}$")
RATE_WINDOW_SECONDS = 10 * 60
SESSION_START_LIMIT = 12
IP_START_LIMIT = 30
SESSION_ACTIVE_LIMIT = 2
SEARCH_OWNER_WATCH_INTERVAL_SECONDS = 0.25
_RATE_LOCK = threading.Lock()
_SESSION_STARTS: dict[str, deque[float]] = defaultdict(deque)
_IP_STARTS: dict[str, deque[float]] = defaultdict(deque)
_JOB_OWNERS: dict[str, str] = {}

NOINDEX_EXACT_PATHS = {
    "/ask.html",
    "/radar.html",
    "/evidence-map.html",
    "/evidence.html",
    "/validation",
    "/review-qa.html",
    "/press-review.html",
    "/regional-routes.html",
    "/strategy.html",
    "/quality.html",
    "/review-routes.html",
    "/ai-context.html",
}
NOINDEX_PATH_PREFIXES = (
    "/validation/",
    "/agent-context/",
    "/synthesis-",
    "/recommendation-",
    "/api/",
)
AGENT_CONTEXT_REQUIRED_FILES = (
    "CONTEXT_MANIFEST.json",
    "SEARCH_STATE.json",
    "SEARCH_SUMMARY.md",
    "ARTICLE_SUMMARIES.jsonl",
)


def _prune_times(values: deque[float], now: float) -> None:
    while values and now - values[0] > RATE_WINDOW_SECONDS:
        values.popleft()


def _mark_job_ownership_status(job_id: str, status: str) -> None:
    with _SEARCH_JOBS_LOCK:
        job = _SEARCH_JOBS.get(job_id)
        if job is not None:
            job["ownership_status"] = status


def _persist_job_owner_when_terminal(job_id: str, owner_scope: str) -> None:
    """Persist search ownership independently from browser polling.

    The search job already runs server-side. This watcher only records the session/search
    relationship after the persisted result exists, so closing the tab or stopping local
    monitoring cannot orphan an otherwise successful search from public history.
    """

    while True:
        try:
            job = _load_search_job(job_id)
        except KeyError:
            return
        status = str(job.get("status") or "")
        if status == "failed":
            _mark_job_ownership_status(job_id, "not_recorded_failed_job")
            return
        if status == "completed":
            search_id = str(job.get("search_id") or "").strip()
            if not search_id:
                _mark_job_ownership_status(job_id, "not_recorded_missing_search_id")
                return
            try:
                record_search_owner(search_id, owner_scope)
            except (OSError, PermissionError, ValueError):
                _mark_job_ownership_status(job_id, "record_failed")
                return
            _mark_job_ownership_status(job_id, "recorded")
            return
        time.sleep(SEARCH_OWNER_WATCH_INTERVAL_SECONDS)


def _start_job_owner_watch(job_id: str, owner_scope: str) -> None:
    thread = threading.Thread(
        target=_persist_job_owner_when_terminal,
        args=(job_id, owner_scope),
        name=f"nutev-search-owner-{job_id[-8:]}",
        daemon=True,
    )
    thread.start()


def _build_metadata() -> dict[str, str]:
    info_path = APP_ROOT / "build-info.json"
    info: dict[str, object] = {}
    if info_path.is_file():
        try:
            parsed = json.loads(info_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                info = parsed
        except (OSError, json.JSONDecodeError):
            info = {}
    # Build identity is baked into the image and must win over a stale server
    # env_file. Environment variables remain a fallback for direct/dev runs.
    return {
        "service": "nutev-web",
        "version": str(info.get("version") or os.environ.get("NUTEV_VERSION") or "dev"),
        "commit": str(info.get("build_commit") or os.environ.get("NUTEV_BUILD_COMMIT") or "unknown"),
        "branch": str(info.get("build_branch") or os.environ.get("NUTEV_BUILD_BRANCH") or "unknown"),
        "build_time": str(info.get("build_time") or os.environ.get("NUTEV_BUILD_TIME") or "unknown"),
        "environment": str(os.environ.get("NUTEV_ENVIRONMENT") or "production"),
    }


def _agent_context_status() -> dict[str, object]:
    """Report Article 1 agent-context availability without probing missing static files.

    The production image mounts the persistent Article 1 bundle into
    ``apps/nutev-web/agent-context/article1``. A clean checkout legitimately has no
    bundle yet, so the public UI needs a stable 200-status capability surface rather
    than generating console 404s or fabricating context.
    """

    root = APP_ROOT / "agent-context" / "article1"
    available: list[str] = []
    missing: list[str] = []
    for name in AGENT_CONTEXT_REQUIRED_FILES:
        path = root / name
        if path.is_file():
            available.append(name)
        else:
            missing.append(name)
    complete = not missing
    return {
        "status": "available" if complete else "not_materialized",
        "available": complete,
        "required_files": list(AGENT_CONTEXT_REQUIRED_FILES),
        "available_files": available,
        "missing_files": missing,
        "base_url": "/agent-context/article1/" if complete else None,
        "semantics": (
            "verified persistent Article 1 agent context is materialized"
            if complete
            else "agent context is not materialized in this runtime; no scientific state is inferred"
        ),
    }


def _should_noindex(path: str) -> bool:
    return path in NOINDEX_EXACT_PATHS or any(path.startswith(prefix) for prefix in NOINDEX_PATH_PREFIXES)


class SecureNutEVHandler(NutEVHandler):
    """Production-facing NutEV handler with browser-session isolation.

    The scientific engine and persisted result files remain unchanged. Public
    history and asynchronous jobs are scoped to a server-issued opaque browser
    session, while legacy/unowned runs stay preserved on disk but are not
    exposed through the public history API.
    """

    server_version = "NutEVWeb/1.1"

    def end_headers(self) -> None:
        pending = getattr(self, "_pending_session_cookie", "")
        if pending:
            secure = self.headers.get("X-Forwarded-Proto", "").lower() == "https" or os.environ.get("NUTEV_ENVIRONMENT") == "production"
            flags = [f"{SESSION_COOKIE}={pending}", "Path=/", "HttpOnly", "SameSite=Lax", "Max-Age=2592000"]
            if secure:
                flags.append("Secure")
            self.send_header("Set-Cookie", "; ".join(flags))
            self._pending_session_cookie = ""
        path = urlparse(self.path).path
        if _should_noindex(path):
            self.send_header("X-Robots-Tag", "noindex, nofollow")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; connect-src 'self'; font-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'; upgrade-insecure-requests",
        )
        super().end_headers()

    def _session_token(self) -> str:
        raw = self.headers.get("Cookie", "")
        cookie = SimpleCookie()
        try:
            cookie.load(raw)
        except Exception:
            cookie = SimpleCookie()
        morsel = cookie.get(SESSION_COOKIE)
        token = morsel.value if morsel else ""
        if not _SESSION_RE.fullmatch(token):
            token = uuid4().hex
            self._pending_session_cookie = token
        return token

    def _owner_scope(self) -> str:
        return sha256(self._session_token().encode("ascii")).hexdigest()

    def _client_ip(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
        return forwarded or str(self.client_address[0])

    def _consume_search_start(self, owner_scope: str) -> tuple[bool, str]:
        now = time.monotonic()
        ip = self._client_ip()
        with _RATE_LOCK, _SEARCH_JOBS_LOCK:
            session_starts = _SESSION_STARTS[owner_scope]
            ip_starts = _IP_STARTS[ip]
            _prune_times(session_starts, now)
            _prune_times(ip_starts, now)
            active = sum(
                1
                for job_id, owner in _JOB_OWNERS.items()
                if owner == owner_scope
                and (_SEARCH_JOBS.get(job_id) or {}).get("status") in {"queued", "running"}
            )
            if active >= SESSION_ACTIVE_LIMIT:
                return False, "Já existem buscas em andamento nesta sessão. Aguarde uma delas terminar."
            if len(session_starts) >= SESSION_START_LIMIT:
                return False, "Limite temporário de novas buscas atingido nesta sessão."
            if len(ip_starts) >= IP_START_LIMIT:
                return False, "Limite temporário de novas buscas atingido para esta origem."
            session_starts.append(now)
            ip_starts.append(now)
        return True, ""

    def _owned_job(self, job_id: str, owner_scope: str) -> dict[str, object]:
        with _RATE_LOCK:
            if _JOB_OWNERS.get(job_id) != owner_scope:
                raise KeyError(job_id)
        job = _load_search_job(job_id)
        search_id = str(job.get("search_id") or "").strip()
        if job.get("status") == "completed" and search_id:
            record_search_owner(search_id, owner_scope)
        return job

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/version":
            self._json(_build_metadata())
            return
        if path == "/api/agent-context/article1/status":
            self._json(_agent_context_status())
            return
        if path == "/api/capabilities":
            self._json(
                {
                    "coordinator_available": self._is_loopback(),
                    "remote_reviewer_available": True,
                    "history_scope": "browser_session",
                }
            )
            return
        if path.startswith("/api/search/jobs/"):
            owner_scope = self._owner_scope()
            job_id = unquote(path[len("/api/search/jobs/"):]).strip()
            try:
                self._json(self._owned_job(job_id, owner_scope))
            except KeyError:
                self._json({"error": "search_job_not_found"}, HTTPStatus.NOT_FOUND)
            return
        if path == "/api/searches":
            owner_scope = self._owner_scope()
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or ["30"])[0])
            except ValueError:
                limit = 30
            runs = list_search_runs(limit=200)
            owned = filter_owned_runs(runs, owner_scope)
            self._json({"searches": owned[: max(1, min(limit, 200))], "scope": "browser_session"})
            return
        if path.startswith("/api/searches/"):
            owner_scope = self._owner_scope()
            search_id = unquote(path[len("/api/searches/"):]).strip()
            if not search_owned_by(search_id, owner_scope):
                self._json({"error": "search_not_found"}, HTTPStatus.NOT_FOUND)
                return
            try:
                self._json(load_search_run(search_id))
            except (FileNotFoundError, ValueError):
                self._json({"error": "search_not_found"}, HTTPStatus.NOT_FOUND)
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/search":
            self._json(
                {
                    "error": "legacy_search_disabled",
                    "message": "Use /api/search/jobs para buscas públicas auditáveis e isoladas por sessão.",
                },
                HTTPStatus.GONE,
            )
            return
        if path == "/api/search/jobs":
            owner_scope = self._owner_scope()
            allowed, message = self._consume_search_start(owner_scope)
            if not allowed:
                self._json({"error": "search_rate_limited", "message": message}, HTTPStatus.TOO_MANY_REQUESTS)
                return
            try:
                payload = self._read_json()
                job = _create_search_job(payload)
            except ValueError as exc:
                self._json({"error": "invalid_request", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            except Exception as exc:
                self._json({"error": "search_failed", "message": f"{type(exc).__name__}: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            job_id = str(job.get("job_id") or "")
            with _RATE_LOCK:
                _JOB_OWNERS[job_id] = owner_scope
            _start_job_owner_watch(job_id, owner_scope)
            self._json(job, HTTPStatus.ACCEPTED)
            return
        super().do_POST()


def main() -> int:
    from http.server import ThreadingHTTPServer
    import argparse

    parser = argparse.ArgumentParser(description="Serve the session-isolated NutEV production web interface.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), SecureNutEVHandler)
    print(f"NutEV secure web disponível em http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
