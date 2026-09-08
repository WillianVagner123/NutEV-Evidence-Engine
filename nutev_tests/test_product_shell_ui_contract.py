from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def text(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_pilot_navigation_uses_tenant_safe_product_surfaces() -> None:
    product = text("product-ui.js")

    assert "href:'/project.html'" in product
    assert "href:'/evidence-library.html'" in product
    assert "href:'/exports.html'" in product
    assert "label:'Buscar evidências'" in product
    assert "if(runtimeMode==='legacy')" in product
    assert "href:'/articles.html'" in product  # legacy compatibility only
    assert "if(location.pathname==='/articles.html')" in product
    assert "location.replace(`/evidence-library.html${suffix}`)" in product


def test_login_surface_is_password_manager_friendly_and_server_backed() -> None:
    html = text("login.html")
    script = text("login.js")

    assert 'autocomplete="username"' in html
    assert 'autocomplete="current-password"' in html
    assert 'type="password"' in html
    assert "/api/auth/status" in script
    assert "/api/auth/me" in script
    assert "/api/auth/login" in script
    assert "credentials:'same-origin'" in script
    assert "raw.startsWith('//')" in script
    assert "url.origin!==location.origin" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script


def test_global_context_shell_exposes_account_context_and_logout_without_browser_storage() -> None:
    script = text("workspace-context.js")

    assert "/api/auth/me" in script
    assert "/api/context" in script
    assert "/api/context/select" in script
    assert "/api/auth/logout" in script
    assert "PROTECTED_PILOT_PATHS" in script
    assert "context-shell-error" in script
    assert "display_name" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert ".style." not in script


def test_home_is_project_first_and_has_no_pilot_link_to_legacy_workbench() -> None:
    html = text("index.html")
    script = text("home-dashboard.js")

    assert 'href="/project.html"' in html
    assert 'href="/evidence-library.html" data-library-link' in html
    assert "home-dashboard.js" in html
    assert "/api/application" in script
    assert "/api/context/select" in script
    assert "libraryLinks.forEach(link=>link.href='/articles.html')" in script  # legacy branch
    assert "libraryLinks.forEach(link=>link.href='/evidence-library.html')" in script


def test_project_hub_consumes_application_layer_without_inventing_scientific_state() -> None:
    html = text("project.html")
    script = text("project-page.js")

    assert "Aplicação de pesquisa" in html
    assert "/api/application/templates" in script
    assert "/api/application" in script
    assert "SCOPING_REVIEW" in script
    assert "INTEGRATIVE_REVIEW" in script
    assert "/search.html" in script
    assert "/evidence-library.html" in script
    assert "/exports.html" in script
    assert "PRISMA" in html
    assert "discovery" not in script.casefold()
    assert "formal search" not in script.casefold()


def test_exports_surface_is_read_only_from_ui_and_shows_audit_integrity() -> None:
    html = text("exports.html")
    script = text("exports-page.js")

    assert "/api/exports" in script
    assert "/api/audit?limit=50" in script
    assert "/manifest" in script
    assert "/artifacts/" in script
    assert "chain_valid" in script
    assert "method:'POST'" not in script
    assert "Exportar ou baixar um artefato não muda" in html


def test_library_ui_uses_researcher_language_and_hides_internal_identity_form() -> None:
    html = text("evidence-library.html")
    script = text("evidence-library-page.js")

    assert "Biblioteca de evidências" in html
    assert "Adicionar por ID canônico — opção técnica" in html
    assert "Guardar na Biblioteca" in html
    assert "Salvar placement" not in html
    assert "grant" not in html.casefold()
    assert "placement(s)" not in script
    assert "Remover da biblioteca" in script
    assert "STATE_LABELS" in script
    assert "libraryFilter" in script
    assert "libraryStateFilter" in script


def test_search_library_routes_open_action_to_tenant_library_in_pilot() -> None:
    script = text("search-library-ui.js")

    assert "canonicalLibraryHref" in script
    assert "'/evidence-library.html'" in script
    assert "Abrir na Biblioteca" in script
    assert "outcome.scope==='project'" in script
    assert "CORE local" not in script


def test_pilot_disables_cross_project_browser_strategy_state() -> None:
    product = text("product-ui.js")

    assert "let strategyFlowEnabled=false" in product
    assert "strategyFlowEnabled=runtimeMode==='legacy'" in product
    assert "if(!strategyFlowEnabled)return{}" in product
    assert "if(!strategyFlowEnabled||!STRATEGY_FLOW_KEYS.includes(step))return null" in product
    assert "estados locais do navegador ficam desativados" in product


def test_product_css_has_keyboard_motion_and_mobile_navigation_guards() -> None:
    css = text("product-ui.css")

    assert ":focus-visible" in css
    assert "prefers-reduced-motion:reduce" in css
    assert ".mobile-nav-toggle" in css
    assert ".sidebar.mobile-nav-open nav" in css
    assert "min-height:42px" in css
    assert ".context-shell" in css
    assert ".login-shell" in css
