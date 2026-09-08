from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"
API = WEB / "article1_d132_api.py"
PAGE = WEB / "review-d132.html"
CLIENT = WEB / "review-d132.js"
ROUTES = WEB / "tenant_platform_routes.py"
ASSEMBLY = ROOT / "src" / "nutev" / "applications" / "willian_doctorate_a1" / "d132.py"


def test_private_link_uses_fragment_and_guest_client_keeps_token_in_memory_only() -> None:
    api = API.read_text(encoding="utf-8")
    client = CLIENT.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")

    assert '"/review-d132.html#token="' in api
    assert "window.location.hash" in client
    assert "URLSearchParams(window.location.hash.slice(1))" in client
    assert "window.history.replaceState" in client
    assert 'headers.set("Authorization", `Bearer ${reviewToken}`)' in client
    assert 'cache: "no-store"' in client
    assert '?token=' not in api
    assert '?token=' not in client
    assert '?token=' not in page
    for forbidden_storage in (
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "document.cookie",
    ):
        assert forbidden_storage not in client


def test_guest_surface_does_not_embed_blinded_scientific_fields() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8").casefold()
        for path in (API, PAGE, CLIENT)
    )
    for forbidden in (
        "r1_decision",
        "nutev_rank",
        "nutev_score",
        "machine_relevance",
        "other_reviewer_decision",
    ):
        assert forbidden not in sources


def test_api_requires_active_article1_scoping_assembly_not_any_scoping_project() -> None:
    source = API.read_text(encoding="utf-8")
    assert 'ASSEMBLY_ID = "WILLIAN_DOCTORATE_A1"' in source
    assert 'descriptor.get("template_id") != SCOPING_REVIEW' in source
    assert 'configuration.get("assembly_id") != ASSEMBLY_ID' in source
    assert 'configuration.get("d132_config_version") != _service().config().config_version' in source
    assert '"article1_application_required"' in source


def test_every_guest_operation_re_resolves_bearer_token_through_service() -> None:
    source = ASSEMBLY.read_text(encoding="utf-8")
    assert "def _guest_access(self, token: str):" in source
    assert "access = self.engine.access_for_guest(token)" in source
    assert "def guest_payload(self, token: str)" in source
    assert "def save_guest_decision(" in source
    assert "def submit_guest(self, token: str)" in source
    # Each public guest operation calls _guest_access instead of accepting a cached ReviewerAccess.
    assert source.count("self._guest_access(token)") >= 3


def test_d132_routes_are_installed_only_as_application_extension() -> None:
    routes = ROUTES.read_text(encoding="utf-8")
    assert "from article1_d132_api import install_article1_d132_routes" in routes
    assert "install_article1_d132_routes()" in routes
    engine = (ROOT / "src" / "nutev" / "review" / "engine.py").read_text(encoding="utf-8").casefold()
    assert "article1_d132" not in engine
    assert "willian_doctorate_a1" not in engine


def test_guest_page_is_noindex_and_has_no_inline_script() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex,nofollow,noarchive">' in page
    assert '<script src="/review-d132.js" defer></script>' in page
    assert "<script>" not in page
