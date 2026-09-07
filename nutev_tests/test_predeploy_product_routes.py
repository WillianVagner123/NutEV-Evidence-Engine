from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"
VALIDATION = ROOT / "apps" / "nutev-validation"
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']')


def _internal_target_exists(href: str) -> bool:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return True
    path = parsed.path
    if not path:
        return True
    if path == "/":
        return (WEB / "index.html").is_file()
    if path in {"/validation", "/validation/"}:
        return (VALIDATION / "index.html").is_file()
    if path.startswith("/api/"):
        return True
    relative = path.lstrip("/")
    candidate = WEB / relative
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate.is_file()


def test_all_static_internal_links_resolve_to_a_real_surface() -> None:
    failures: list[str] = []
    for page in sorted(WEB.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        for href in _HREF_RE.findall(text):
            if not _internal_target_exists(href):
                failures.append(f"{page.name} -> {href}")
    assert not failures, "broken internal links:\n" + "\n".join(failures)


def test_canonical_navigation_targets_exist() -> None:
    ui = (WEB / "product-ui.js").read_text(encoding="utf-8")
    for href in ("/", "/search.html", "/articles.html", "/search.html?view=history", "/advanced.html"):
        assert f"href:'{href}'" in ui
        assert _internal_target_exists(href), href


def test_critical_search_ctas_have_explicit_handlers() -> None:
    html = (WEB / "search.html").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")

    for element_id in ("searchBtn", "globalSearchBtn", "compileStrategyBtn", "refreshHistory"):
        assert f'id="{element_id}"' in html
        assert f"$('#{element_id}')" in app
    assert "$('#searchBtn').onclick=()=>runSearch()" in app
    assert "$('#globalSearchBtn').onclick=()=>runSearch({global:true})" in app
    assert "$('#compileStrategyBtn').onclick=compileStrategyPreview" in app
    assert "$('#refreshHistory').onclick=renderHistory" in app


def test_core_search_controls_are_keyboard_and_accessibility_addressable() -> None:
    html = (WEB / "search.html").read_text(encoding="utf-8")

    assert 'role="radiogroup" aria-label="Modo de busca"' in html
    assert 'role="alert" aria-live="assertive"' in html
    assert 'role="status" aria-live="polite"' in html
    assert 'class="skip-link"' in html
    assert 'aria-describedby="globalSearchNote"' in html
