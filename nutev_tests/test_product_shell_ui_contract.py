from pathlib import Path
import re


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

    # The hub now shows the Article 1 gate state, so "does not invent scientific state" is no
    # longer keyword absence: it means the verdicts are read from the canonical endpoint and
    # never decided here. The page renders whatever the server derived from the master file.
    assert "/api/article1/scientific-state" in script
    assert "state.gates" in script
    assert "gateStateLabel(gate)" in script

    # No gate verdict may be asserted by the page itself.
    for invented in (
        "press_status",
        "gf10_authorized",
        "query_freeze_complete",
        "formal_provider_search_executed",
        "prisma_search_event_emitted",
    ):
        assert invented not in script, f"project hub must not decide {invented} on its own"

    # Discovery counts must stay labelled as discovery, never as PRISMA or inclusion.
    assert "Não são contagens PRISMA" in script
    assert "Não é busca formal nem contagem PRISMA" in script

    # The only write the hub performs is configuring the project application. It has no write
    # against the Article 1 gate surface, so nothing here can open PRESS, GF-10 or the freeze.
    written_endpoints = set(re.findall(r"jsonFetch\('([^']+)',\{method:'POST'", script))
    assert written_endpoints == {"/api/application"}


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


def test_members_page_manages_access_without_creating_identities_or_moving_ownership() -> None:
    html = text("members.html")
    script = text("members-page.js")

    assert "/api/workspace/members" in script
    assert "/api/workspace/members/status" in script
    assert "ACADEMIC_SUPERVISOR" in script
    assert "Professor orientador" in script

    # The page states the two boundaries it must never cross.
    assert "nunca cria conta nem define senha de outra pessoa" in html
    assert "A propriedade do workspace nunca muda por esta tela." in html

    # WORKSPACE_OWNER is never offered: the role list comes from the server's assignable set.
    assert "assignable_roles" in script
    assert "WORKSPACE_OWNER:'Proprietário'" in script  # label only, for display
    assert "value=\"WORKSPACE_OWNER\"" not in html

    # A role change is never silent.
    assert "allow_role_change" in script
    assert "window.confirm" in script

    # Membership management is not scientific approval.
    assert "não é aprovação científica" in html.casefold()


def test_project_hub_renders_only_the_actions_the_role_can_actually_use() -> None:
    """Forbidden actions are not drawn, rather than drawn and refused with 403 on click."""
    script = text("project-page.js")

    assert "ROLE_CAPABILITIES" in script
    assert "const NO_CAPABILITIES" in script

    # An unknown or absent role falls back to no capabilities, not to full ones.
    assert "ROLE_CAPABILITIES[role]||NO_CAPABILITIES" in script

    # The supervisor's capability row must stay read-only.
    supervisor = re.search(r"ACADEMIC_SUPERVISOR:\{([^}]*)\}", script)
    assert supervisor is not None
    flags = dict(
        (key.strip(), value.strip() == "true")
        for key, value in (pair.split(":", 1) for pair in supervisor.group(1).split(","))
    )
    assert flags["search"] is False
    assert flags["libraryWrite"] is False
    assert flags["review"] is False
    assert flags["applicationManage"] is False
    assert flags["membersManage"] is False

    # Member administration is reachable only when the role carries it.
    assert "if(capabilities.membersManage)$('#adminSection').classList.remove('hidden')" in script

    # And the UI never claims to be the authority.
    assert "never what is allowed" in script
