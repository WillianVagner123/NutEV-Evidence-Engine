from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_review_brief_and_ask_wire_shared_research_flow() -> None:
    for page in ("synthesis-review.html", "synthesis-brief.html", "ask.html"):
        html = read(page)
        assert 'src="./synthesis-flow.js"' in html

    script = read("synthesis-flow.js")
    assert "Human Synthesis Review" in script
    assert "Verified Synthesis Brief" in script
    assert "Ask NutEV" in script
    assert "Do julgamento humano ao retrieval grounded — sem promoção automática" in script
    assert "./synthesis-flow.css" in script


def test_shared_flow_is_navigation_only_and_does_not_add_scientific_io() -> None:
    script = read("synthesis-flow.js")

    assert "navigation only" in script
    assert "Review, Brief e Ask são superfícies distintas" in script
    assert "Ask NutEV não importa automaticamente decisões do Review nem o Brief" in script
    assert "canonical synthesis" in script
    assert "EvidenceClaim" in script
    assert "PRESS" in script
    assert "GF-10" in script
    assert "PRISMA" in script
    assert "fetch(" not in script
    assert "XMLHttpRequest" not in script
    assert "method:'POST'" not in script
    assert 'method: "POST"' not in script


def test_current_stage_is_not_a_duplicate_navigation_link() -> None:
    script = read("synthesis-flow.js")

    assert 'aria-current="step"' in script
    assert 'data-synthesis-flow-target' in script
    assert '<a ' not in script
    assert "location.assign" in script


def test_review_flow_reuses_existing_human_review_controls() -> None:
    script = read("synthesis-flow.js")

    assert "#reviewerName" in script
    assert "#reviewProgress" in script
    assert "#reviewLedger" in script
    assert "#exportReview" in script
    assert "Exportar revisão" in script
    assert "SHA-256 e context fingerprint serão verificados novamente" in script
    assert "canonical:false" in script


def test_brief_flow_remains_fail_closed_and_does_not_feed_ask() -> None:
    script = read("synthesis-flow.js")

    assert "#briefHealth" in script
    assert "#verificationGrid" in script
    assert "#exportBrief" in script
    assert "Importe um Review exportado para executar a verificação fail-closed" in script
    assert "Nenhum relation label, rationale, SHA do Brief ou decisão humana é enviado ao Ask" in script
    assert "integrity verified ≠ scientifically validated" in script


def test_ask_flow_is_grounded_retrieval_only() -> None:
    script = read("synthesis-flow.js")
    ask = read("ask.js")

    assert "#askHealth" in script
    assert "#askResultMeta" in script
    assert "#selectedCount" in script
    assert "#contextPacket" in script
    assert "#buildPacket" in script
    assert "0 chamadas externas de LLM" in script
    assert "Ask NutEV não lê o Review nem o Brief" in script
    assert "api.openai.com" not in ask
    assert "api.anthropic.com" not in ask


def test_synthesis_flow_is_responsive_and_keyboard_native() -> None:
    script = read("synthesis-flow.js")
    styles = read("synthesis-flow.css")

    assert '<button type="button" class="synthesis-flow-stage"' in script
    assert '<button type="button" class="synthesis-flow-action' in script
    assert "@media(max-width:900px)" in styles
    assert "@media(max-width:640px)" in styles
    assert ":focus-visible" in styles


def test_visual_flow_does_not_hardcode_production_snapshot_counts() -> None:
    script = read("synthesis-flow.js")
    for forbidden in ("33067", "33839", "41139", "662", "504", "316", "85"):
        assert forbidden not in script
