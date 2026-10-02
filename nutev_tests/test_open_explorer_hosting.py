"""The Open Evidence Explorer is public on the hosted runtime; everything private stays closed.

Runs the real pilot HTTP server (tools/pilot_closeout_fixture.py) as an anonymous visitor.
"""

from __future__ import annotations

import http.client
from pathlib import Path
import sys
from urllib.parse import urlsplit

import pytest

from tools.pilot_closeout_fixture import pilot_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "nutev-web"))
from request_boundary import canonical_request_path, is_open_explorer_path, pilot_route_kind  # noqa: E402

OPEN_APIS = {
    "https://www.ebi.ac.uk",
    "https://api.openalex.org",
    "https://api.crossref.org",
    "https://eutils.ncbi.nlm.nih.gov",
}


@pytest.fixture(scope="module")
def live():
    with pilot_server() as fixture:
        yield fixture


def call(base: str, path: str, method: str = "GET") -> tuple[int, bytes, dict[str, str]]:
    addr = urlsplit(base)
    conn = http.client.HTTPConnection(addr.hostname, addr.port, timeout=10)
    conn.request(method, path)
    res = conn.getresponse()
    raw = res.read()
    out = (res.status, raw, dict(res.getheaders()))
    conn.close()
    return out


def _directives(csp: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for part in csp.split(";"):
        bits = part.strip().split()
        if bits:
            out[bits[0]] = set(bits[1:])
    return out


def test_route_classification_is_narrow():
    assert pilot_route_kind("/aberto") == "static"
    assert pilot_route_kind("/aberto/") == "static"
    assert pilot_route_kind("/aberto/app.js") == "static"
    assert pilot_route_kind("/aberto/data/nutev-open-data.js") == "static"
    assert pilot_route_kind("/aberto/presentation.json") == "blocked"
    assert pilot_route_kind("/aberto/README.md") == "blocked"
    assert not is_open_explorer_path("/abertos/x.js")
    assert not is_open_explorer_path("/api/aberto")
    with pytest.raises(ValueError):
        canonical_request_path("/aberto/../server.py")


def test_anonymous_visitor_gets_the_open_explorer_without_login(live):
    base = live[0]
    status, _raw, headers = call(base, "/aberto")
    assert status == 301 and headers["Location"].endswith("/aberto/")

    status, raw, headers = call(base, "/aberto/")
    assert status == 200
    assert b"Explorador Aberto" in raw and b'src="planner.js"' in raw
    assert "nutev_auth_session" not in headers.get("Set-Cookie", "")

    for asset in ("app.js", "core.js", "planner.js", "sources.js", "i18n.js", "styles.css", "data/nutev-open-data.js"):
        status, raw, _ = call(base, "/aberto/" + asset)
        assert status == 200 and raw, asset


def test_open_explorer_csp_only_widens_connect_src_for_that_path(live):
    base = live[0]
    _, _, open_headers = call(base, "/aberto/")
    csp = _directives(open_headers["Content-Security-Policy"])
    assert csp["connect-src"] == {"'self'"} | OPEN_APIS
    assert csp["script-src"] == {"'self'"}
    assert csp["object-src"] == {"'none'"}

    _, _, app_headers = call(base, "/login.html")
    other = _directives(app_headers["Content-Security-Policy"])
    assert other["connect-src"] == {"'self'"}


def test_private_surfaces_stay_closed_for_anonymous_visitors(live):
    base = live[0]
    for path in ("/api/library", "/api/search/jobs", "/api/workspace", "/aberto/presentation.json"):
        assert call(base, path)[0] == 401, path


def test_open_explorer_files_contain_no_private_or_backend_hooks():
    for path in (ROOT / "apps" / "nutev-open").rglob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert "/api/" not in text, path
        assert "document.cookie" not in text, path


def test_edge_and_entry_points_link_the_public_search():
    caddy = (ROOT / "deploy" / "hetzner" / "Caddyfile").read_text(encoding="utf-8")
    assert "@protected not path /aberto /aberto/*" in caddy
    assert "basic_auth @protected {" in caddy
    home = (ROOT / "apps" / "nutev-web" / "home-dashboard.js").read_text(encoding="utf-8")
    login = (ROOT / "apps" / "nutev-web" / "login.html").read_text(encoding="utf-8")
    assert 'href="/aberto/"' in home
    assert 'href="/aberto/"' in login


def login_cookie(base: str, user: dict) -> str:
    import json

    addr = urlsplit(base)
    conn = http.client.HTTPConnection(addr.hostname, addr.port, timeout=10)
    conn.request(
        "POST",
        "/api/auth/login",
        json.dumps({"email": user["email"], "password": user["password"]}),
        {"Content-Type": "application/json"},
    )
    res = conn.getresponse()
    res.read()
    cookie = res.getheader("Set-Cookie", "").split(";")[0]
    conn.close()
    assert res.status == 200 and cookie
    return cookie


def test_anonymous_root_goes_to_open_search_and_members_keep_their_home(live):
    base, data, _ = live
    for path in ("/", "/index.html"):
        status, _raw, headers = call(base, path)
        assert status == 302 and headers["Location"] == "/aberto/", path
    assert call(base, "/login.html")[0] == 200

    cookie = login_cookie(base, data["users"]["a"])
    addr = urlsplit(base)
    conn = http.client.HTTPConnection(addr.hostname, addr.port, timeout=10)
    conn.request("GET", "/", headers={"Cookie": cookie})
    res = conn.getresponse()
    body = res.read()
    conn.close()
    assert res.status == 200 and b"tenant-session.js" in body

    stale = call_with_cookie(base, "/", "nutev_auth_session=not-a-real-session")
    assert stale[0] == 302


def call_with_cookie(base: str, path: str, cookie: str) -> tuple[int, dict[str, str]]:
    addr = urlsplit(base)
    conn = http.client.HTTPConnection(addr.hostname, addr.port, timeout=10)
    conn.request("GET", path, headers={"Cookie": cookie})
    res = conn.getresponse()
    res.read()
    out = (res.status, dict(res.getheaders()))
    conn.close()
    return out
