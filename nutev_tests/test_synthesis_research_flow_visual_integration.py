from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_review_summary_and_query_wire_shared_research_flow() -> None:
    for page in ("synthesis-review.html", "synthesis-brief.html", "ask.html"):
        html = read(page)
        assert 'src="./synthesis-flow.js"' in html

    script = read("synthesis-flow.js")
    assert "Revisão de Síntese" in script
    assert "Resumo de Síntese Verificado" in script
    assert "Consulta de Evidências" in script
    assert "Da revisão humana à consulta vinculada às fontes — sem promoção automática" in script
    assert "./synthesis-flow.css" in script


def test_shared_flow_is_navigation_only_and_does_not_add_scientific_io() -> None:
    script = read("synthesis-flow.js")

    assert "navigation only" in script
    assert "Revisão, Resumo e Consulta são superfícies distintas" in script
    assert "A Consulta de Evidências não importa automaticamente decisões da Revisão nem do Resumo" in script
    assert "síntese canônica" in script
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
    assert "SHA-256 e a impressão digital do contexto serão verificados novamente" in script
    assert "canonical:false" in script


def test_summary_flow_remains_fail_closed_and_does_not_feed_query() -> None:
    script = read("synthesis-flow.js")

    assert "#briefHealth" in script
    assert "#verificationGrid" in script
    assert "#exportBrief" in script
    assert "Importe uma Revisão exportada para executar a verificação com bloqueio por segurança" in script
    assert "Nenhum rótulo de relação, justificativa, SHA do Resumo ou decisão humana é enviado à Consulta" in script
    assert "integridade verificada ≠ validado cientificamente" in script


def test_evidence_query_flow_is_deterministic_and_source_linked() -> None:
    script = read("synthesis-flow.js")
    ask = read("ask.js")

    assert "#askHealth" in script
    assert "#askResultMeta" in script
    assert "#selectedCount" in script
    assert "#contextPacket" in script
    assert "#buildPacket" in script
    assert "Consulta determinística sobre o contexto verificado" in script
    assert "A Consulta de Evidências não lê a Revisão nem o Resumo" in script
    assert "api.openai.com" not in ask
    assert "api.anthropic.com" not in ask
    assert "method:'POST'" not in ask.replace(" ", "")


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
