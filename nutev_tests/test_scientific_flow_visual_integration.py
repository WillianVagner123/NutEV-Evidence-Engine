from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_three_scientific_surfaces_wire_shared_visual_flow() -> None:
    for page in ("evidence-map.html", "intelligence.html", "review.html"):
        html = read(page)
        assert 'href="./scientific-flow.css"' in html
        assert 'src="./scientific-flow.js"' in html

    script = read("scientific-flow.js")
    assert "Evidence Map" in script
    assert "Scientific Intelligence" in script
    assert "Human Review" in script
    assert "Do mapa à decisão humana, sem atalhos científicos" in script


def test_current_flow_stage_is_indicator_not_duplicate_self_link() -> None:
    script = read("scientific-flow.js")

    assert "stage.id===flowStage" in script
    assert 'class="scientific-flow-stage active" aria-current="step"' in script
    assert "document.querySelectorAll('a[data-flow-stage]')" in script


def test_visual_flow_preserves_scientific_boundaries() -> None:
    script = read("scientific-flow.js")

    assert "Nenhum filtro, volume, recorrência ou clique cria elegibilidade" in script
    assert "EvidenceClaim" in script
    assert "decisão de Review" in script
    assert "PRISMA" in script
    assert "não é força da evidência" in script
    assert "não é taxa de inclusão nem resultado científico" in script


def test_evidence_map_passes_only_navigation_context_to_intelligence() -> None:
    script = read("scientific-flow.js")

    assert "#mapDomainFilter" in script
    assert "/intelligence.html?domain=" in script
    assert "mapClassFilter" in script
    assert "mapRouteFilter" in script
    assert "Levar domínio para Intelligence" in script
    assert "fetch(" not in script


def test_intelligence_visual_overview_reuses_existing_domain_selection() -> None:
    script = read("scientific-flow.js")

    assert "scientificDomainOverview" in script
    assert "data-flow-domain" in script
    assert "data-select-domain" in script
    assert "dispatchEvent(new Event('change',{bubbles:true}))" in script
    assert "result bundle materializado" in script
    assert "CSS.escape" in script


def test_review_progress_is_read_only_visual_state() -> None:
    script = read("scientific-flow.js")
    review = read("review.html")

    assert "reviewVisualProgress" in script
    assert "assignmentRoundMeta" in script
    assert "assignmentList" in script
    assert "Progresso operacional da atribuição" in script
    assert "O recorte visual anterior não é importado como decisão" in script
    assert "/api/review/decision" not in script
    assert "/api/review/submit" not in script
    assert "method:'POST'" not in script
    assert 'src="./review-control.js"' in review
    assert "tenant-session.js" in review


def test_scientific_flow_is_responsive_and_uses_native_buttons() -> None:
    script = read("scientific-flow.js")
    styles = read("scientific-flow.css")

    assert '<button type="button" class="scientific-domain-bar' in script
    assert "role=\"progressbar\"" in script
    assert "@media(max-width:900px)" in styles
    assert "@media(max-width:640px)" in styles
    assert ":focus-visible" in styles


def test_visual_flow_does_not_hardcode_production_counts() -> None:
    script = read("scientific-flow.js")
    for forbidden in ("33067", "33839", "41139", "662", "504", "316", "85"):
        assert forbidden not in script
