from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"
VALIDATION = ROOT / "apps" / "nutev-validation"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_core_product_surfaces_load_shared_product_ui() -> None:
    for name in (
        "index.html",
        "search.html",
        "articles.html",
        "evidence.html",
        "evidence-map.html",
        "radar.html",
        "ask.html",
        "review-qa.html",
        "press-review.html",
        "regional-routes.html",
        "advanced.html",
        "scientific-dashboard.html",
    ):
        assert "product-ui.js" in read(WEB / name), name
    assert 'src="/product-ui.js"' in read(VALIDATION / "index.html")


def test_canonical_navigation_is_tenant_aware_and_keeps_advanced_modules_out() -> None:
    script = read(WEB / "product-ui.js")
    nav = script.split("function navGroups()", 1)[1].split("function activeNavKey()", 1)[0]

    # Pilot exposes the research context and tenant-safe product surfaces.
    for label in (
        "Início",
        "Projeto",
        "Buscar evidências",
        "Biblioteca",
        "Exportações",
        "Minhas buscas",
        "Laboratório avançado",
    ):
        assert label in nav
    for href in ("/project.html", "/evidence-library.html", "/exports.html"):
        assert href in nav

    # Legacy keeps its local Workbench without changing the pilot destination.
    assert "if(runtimeMode==='legacy')" in nav
    assert "href:'/articles.html'" in nav

    for hibernated in (
        "Mapa de evidências",
        "Radar",
        "Perguntar ao corpus",
        "PRESS",
        "Review Control",
        "Review Routes",
        "Validação científica",
        "QA",
    ):
        assert hibernated not in nav
    assert "normalizeNavigation" in script
    assert 'aria-current="page"' in script
    assert "AI Context" not in nav


def test_search_and_home_present_research_context_without_hiding_search_core() -> None:
    home = read(WEB / "index.html")
    search = read(WEB / "search.html")
    advanced = read(WEB / "advanced.html")

    assert "Nut Evidence Engine" in home
    assert "Contrato científico visível" in home
    assert 'href="/project.html"' in home
    assert 'href="/evidence-library.html"' in home
    assert "Buscar evidências" in search
    assert "Busca avançada" in search
    assert "Modo revisão científica" not in search
    assert "Workflow tipo Rayyan / revisão sistemática" in advanced
    assert "uso especializado" in advanced


def test_glossary_explains_search_terms_without_leaking_hibernated_workflows() -> None:
    script = read(WEB / "product-ui.js")
    css = read(WEB / "product-ui.css")
    glossary = script.split("const GLOSSARY=", 1)[1].split("const STRATEGY_FLOW_STORAGE_KEY", 1)[0]
    for term in (
        "Busca progressiva",
        "Provider",
        "Deduplicação",
        "Ranking",
        "Proveniência",
        "Workspace",
        "Projeto",
        "Aplicação de pesquisa",
    ):
        assert term in glossary
    for hidden in ("PRESS", "PRISMA", "EvidenceClaim", "EvidenceSet", "Freeze"):
        assert hidden not in glossary
    assert "code,pre,script,style,textarea" in script
    assert "glossary-trigger" in css
    assert "glossary-dialog" in css


def test_strategy_pages_form_one_explicit_three_step_flow() -> None:
    qa = read(WEB / "review-qa.html")
    press = read(WEB / "press-review.html")
    regional = read(WEB / "regional-routes.html")

    for page in (qa, press, regional):
        assert 'class="strategy-flow"' in page
        assert "1 · QA" in page
        assert "2 · PRESS" in page
        assert "3 · Rotas regionais" in page

    assert 'aria-current="step"' in qa
    assert 'href="/press-review.html"' in qa
    assert 'aria-current="step"' in press
    assert 'href="/review-qa.html"' in press and 'href="/regional-routes.html"' in press
    assert 'aria-current="step"' in regional
    assert 'href="/validation/"' in regional
