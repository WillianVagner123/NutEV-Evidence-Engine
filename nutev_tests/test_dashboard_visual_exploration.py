from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_dashboard_wires_visual_exploration_layer() -> None:
    home = read("scientific-dashboard.html")
    script = read("dashboard-visual.js")
    styles = read("dashboard-visual.css")

    assert 'src="./dashboard-visual.js"' in home
    assert "dashboard-visual.css" in script
    assert "VISUAL EXPLORATION" in script
    assert "visual-exploration" in styles
    assert "ARTICLE_SUMMARIES.jsonl" in script


def test_visual_layer_cross_filters_existing_dashboard_controls() -> None:
    script = read("dashboard-visual.js")

    assert "data-visual-filter" in script
    assert "setDashboardFilter" in script
    assert "filterProvider" in script
    assert "filterYear" in script
    assert "filterFullText" in script
    assert "dispatchEvent(new Event('change',{bubbles:true}))" in script
    assert "history.pushState" not in script


def test_visual_layer_keeps_scientific_interpretation_boundaries() -> None:
    script = read("dashboard-visual.js")

    assert "não representam qualidade, certeza ou força da evidência" in script
    assert "Cross-filter é apenas navegação analítica" in script
    assert "Nenhum clique altera Review" in script
    assert "PRESS, GF-10 ou PRISMA" in script
    assert "volume não implica tendência causal" in script


def test_visual_layer_uses_verified_tier_a_without_hardcoded_production_counts() -> None:
    script = read("dashboard-visual.js")

    for forbidden in ("33067", "33839", "41139", "662", "504", "316", "85"):
        assert forbidden not in script

    assert "fetch('/agent-context/article1/ARTICLE_SUMMARIES.jsonl'" in script
    assert "formatPercent" in script
    assert "source_provider" in script
    assert "full_text_status" in script


def test_visual_controls_are_keyboard_native_and_responsive() -> None:
    script = read("dashboard-visual.js")
    styles = read("dashboard-visual.css")

    assert '<button type="button" class="segment' in script
    assert '<button type="button" class="visual-bar' in script
    assert '<button type="button" class="route-tile' in script
    assert '<button type="button" class="pulse-bar' in script
    assert "@media(max-width:700px)" in styles
    assert "@media(max-width:470px)" in styles
