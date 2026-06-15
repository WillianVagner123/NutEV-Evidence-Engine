"""SSRF and resource-exhaustion guards for outbound HTTP in NutEV/NutMEV.

The pipeline fetches URLs that originate from untrusted search results, scraped
publisher pages and DOI redirects. Without guards, a malicious or compromised
page can redirect the crawler at internal/loopback hosts (e.g. the cloud
metadata endpoint ``169.254.169.254``) or stream an unbounded body to exhaust
memory/disk. This module centralizes:

* scheme allow-listing (http/https only);
* DNS resolution with rejection of private/loopback/link-local/reserved IPs;
* manual redirect following that re-validates every hop;
* a hard cap on the number of bytes read from a response.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests

ALLOWED_SCHEMES = {"http", "https"}
DEFAULT_MAX_BYTES = 25 * 1024 * 1024  # 25 MB
DEFAULT_MAX_REDIRECTS = 5


class UnsafeURLError(ValueError):
    """Raised when a URL is not safe to fetch (bad scheme or non-public host)."""


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return _is_blocked_ip(ip.ipv4_mapped)
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def assert_public_url(url: str) -> str:
    """Validate that ``url`` uses http(s) and resolves only to public addresses.

    Returns the URL unchanged when safe; raises :class:`UnsafeURLError` otherwise.
    """
    parsed = urlparse(url or "")
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"blocked URL scheme: {scheme or '(none)'!r}")
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL has no host")

    # A bare IP literal is validated directly; otherwise resolve every address
    # the hostname maps to and reject if any is non-public.
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if _is_blocked_ip(literal):
            raise UnsafeURLError(f"host {host!r} is a non-public address")
        return url

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"cannot resolve host {host!r}") from exc
    if not infos:
        raise UnsafeURLError(f"cannot resolve host {host!r}")
    for info in infos:
        addr = info[4][0].split("%")[0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError as exc:
            raise UnsafeURLError(f"invalid resolved address {addr!r}") from exc
        if _is_blocked_ip(ip):
            raise UnsafeURLError(f"host {host!r} resolves to non-public address {ip}")
    return url


def is_public_url(url: str) -> bool:
    """Return True when :func:`assert_public_url` would accept ``url``."""
    try:
        assert_public_url(url)
        return True
    except UnsafeURLError:
        return False


def _read_capped(response: requests.Response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(8192):
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes:
            response.close()
            raise UnsafeURLError(f"response body exceeds max_bytes ({max_bytes})")
        chunks.append(chunk)
    return b"".join(chunks)


def safe_get(
    url: str,
    *,
    timeout: float | tuple[float, float] = 20,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    headers: dict | None = None,
    session: requests.Session | None = None,
) -> requests.Response:
    """SSRF-safe ``requests.get`` with per-hop validation and a body size cap.

    Redirects are followed manually so each target is re-validated against the
    private-IP block list; the response body is read with a hard byte cap. The
    returned response has its content materialized (``.content``/``.text`` work).
    """
    own_session = session is None
    session = session or requests.Session()
    try:
        current = url
        for _ in range(max_redirects + 1):
            assert_public_url(current)
            response = session.get(
                current,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
                headers=headers,
            )
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                response.close()
                if not location:
                    return response
                current = urljoin(current, location)
                continue
            response._content = _read_capped(response, max_bytes)
            return response
        raise UnsafeURLError(f"too many redirects (> {max_redirects})")
    finally:
        if own_session:
            session.close()
