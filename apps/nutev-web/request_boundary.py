"""Pilot HTTP boundary. No scientific state, network or tenant inference."""
from __future__ import annotations

from pathlib import PurePosixPath
import re
from urllib.parse import unquote, urlsplit

PUBLIC_API = frozenset({
    "/api/health", "/api/version", "/api/providers", "/api/capabilities",
    "/api/auth/status", "/api/auth/login", "/api/auth/logout", "/api/auth/me",
    "/api/context", "/api/context/select", "/api/query/compile",
})
TENANT_PREFIXES = (
    "/api/search/jobs", "/api/searches", "/api/library", "/api/application",
    "/api/exports", "/api/audit", "/api/article2/integrative",
)
A1_CONTEXT_FILES = frozenset({
    "CONTEXT_MANIFEST.json", "SEARCH_STATE.json", "SEARCH_SUMMARY.md", "ARTICLE_SUMMARIES.jsonl",
})
STATIC_SUFFIXES = frozenset({".html", ".css", ".js", ".ico", ".svg", ".png", ".jpg", ".webp", ".woff", ".woff2"})


def canonical_request_path(target: str) -> str:
    raw = urlsplit(target).path
    if re.search(r"%(?![0-9a-fA-F]{2})", raw):
        raise ValueError("malformed escape")
    path = unquote(raw, errors="strict")
    # SimpleHTTPRequestHandler also decodes: no second interpretation allowed.
    if unquote(path) != path or re.search(r"%2[fF]|%5[cC]", raw):
        raise ValueError("ambiguous encoded path")
    if not path.startswith("/") or "\\" in path or "//" in path:
        raise ValueError("ambiguous separator")
    if any(part in {".", ".."} for part in path.split("/")):
        raise ValueError("dot segment")
    if any(ord(c) < 32 or ord(c) == 127 for c in path):
        raise ValueError("control character")
    return path


def pilot_route_kind(path: str) -> str:
    if path in PUBLIC_API:
        return "public_api"
    if path == "/api/article1/d132" or path.startswith("/api/article1/d132/"):
        return "guest_scoped"  # Its existing adapter checks the scoped guest credential.
    if any(path == p or path.startswith(p + "/") for p in TENANT_PREFIXES):
        return "private_api"
    if path.startswith("/api/"):
        return "blocked"  # Legacy science/workbench/loopback is not tenant authorization.
    if path.startswith("/agent-context/article1/"):
        name = path.removeprefix("/agent-context/article1/")
        return "article1_context" if name in A1_CONTEXT_FILES else "blocked"
    if path in {"/", "/index.html", "/login.html", "/validation/"}:
        return "static"
    parts = PurePosixPath(path).parts
    if any(p.startswith(".") for p in parts) or PurePosixPath(path).suffix not in STATIC_SUFFIXES:
        return "blocked"  # No directory listing, source, database, manifest or private asset.
    return "static"


def same_origin_write(headers, *, secure: bool) -> bool:
    site = str(headers.get("Sec-Fetch-Site", "")).lower()
    if site == "cross-site":
        return False
    origin = headers.get("Origin")
    if origin is not None:
        parsed = urlsplit(origin)
        scheme = "https" if secure else "http"
        if parsed.scheme != scheme or parsed.netloc.lower() != str(headers.get("Host", "")).lower():
            return False
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username:
            return False
    # Non-browser clients are allowed, but form content cannot invoke JSON writes.
    content_type = str(headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
    return content_type == "application/json" or (
        not content_type and str(headers.get("Content-Length", "0")) == "0"
    )
