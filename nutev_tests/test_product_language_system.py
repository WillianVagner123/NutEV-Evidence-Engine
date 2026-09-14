from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"
VALIDATION = ROOT / "apps" / "nutev-validation"
DOC = ROOT / "docs" / "PRODUCT_LANGUAGE_SYSTEM.md"


PRIMARY_PRODUCT_SURFACES = (
    "login.html",
    "project.html",
    "exports.html",
    "search.html",
    "evidence-library.html",
    "articles.html",
    "evidence.html",
    "evidence-map.html",
    "radar.html",
    "review.html",
    "review-routes.html",
    "review-qa.html",
    "press-review.html",
    "regional-routes.html",
    "quality.html",
    "strategy.html",
    "scientific-dashboard.html",
    "advanced.html",
    "ask.html",
    "ask.js",
    "ai-context.html",
    "ai-context.js",
    "intelligence.html",
    "intelligence.js",
    "scientific-flow.js",
    "evidence-interpretation.js",
    "synthesis-flow.js",
    "synthesis-review.html",
    "synthesis-brief.html",
)

# Explicit technical debt inventory. Files leave this set as the canonical shell
# pass reaches each scientific/governance surface. The test prevents new debt from
# appearing silently outside this reviewed list.
LEGACY_PRESENTATION_ALLOWLIST = {
    "claim-appraisal.html",
    "evidence-claims.html",
    "evidence-sets.html",
    "recommendation-candidates.html",
    "recommendation-human-validation.html",
    "synthesis-governance.html",
    "synthesis-publication.html",
    "synthesis-release.html",
}

FORBIDDEN_PRODUCT_LABELS = (
    "Evidence Engine",
    "Scientific Intelligence",
    "Ask NutEV",
    "AI Context",
    "Human Synthesis Review",
    "Human Synthesis Brief",
    "Grounded retrieval",
    "retrieval grounded",
    "Prompt canônico para agentes",
    "INSTRUCTIONS FOR THE ANALYZING AGENT",
    "Evidence first. Generation second.",
)


def read_web(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def presentation_source() -> str:
    return "\n".join(read_web(name) for name in PRIMARY_PRODUCT_SURFACES)


def html_legacy_debt() -> dict[str, set[str]]:
    debt: dict[str, set[str]] = {}
    for root in (WEB, VALIDATION):
        for path in root.glob("*.html"):
            source = path.read_text(encoding="utf-8")
            hits = {label for label in FORBIDDEN_PRODUCT_LABELS if label in source}
            if hits:
                debt[path.name] = hits
    return debt


def test_product_surfaces_use_system_first_names() -> None:
    source = presentation_source()

    for expected in (
        "Sistema de Evidências Científicas",
        "Análise de Evidências",
        "Consulta de Evidências",
        "Contexto de Evidências",
        "Pacote de evidências",
        "Revisão de Síntese",
        "Resumo de Síntese Verificado",
        "Mapa de Evidências",
        "Radar de Evidências",
        "Explorador de Evidências",
        "Observatório de Qualidade",
        "Laboratório de Estratégia",
        "Rotas de Revisão",
        "Controle de qualidade da estratégia",
        "Revisão PRESS",
    ):
        assert expected in source


def test_primary_product_surfaces_do_not_present_legacy_or_llm_branding() -> None:
    source = presentation_source()
    for forbidden in FORBIDDEN_PRODUCT_LABELS:
        assert forbidden not in source


def test_legacy_product_language_is_confined_to_explicit_debt_allowlist() -> None:
    debt = html_legacy_debt()
    unexpected = set(debt) - LEGACY_PRESENTATION_ALLOWLIST
    assert not unexpected, f"Legacy product language escaped allowlist: {sorted(unexpected)}"
    assert set(debt) <= LEGACY_PRESENTATION_ALLOWLIST


def test_validation_entrypoint_uses_system_identity() -> None:
    source = (VALIDATION / "index.html").read_text(encoding="utf-8")
    assert "Sistema de Evidências Científicas" in source
    assert "Evidence Engine" not in source


def test_advanced_lab_uses_system_language_for_secondary_navigation() -> None:
    advanced = read_web("advanced.html")

    for expected in (
        "Sistema de Evidências Científicas",
        "Análise de Evidências",
        "Revisão de Síntese",
        "Resumo de Síntese",
        "Consulta de Evidências",
        "Explorador de Evidências",
        "Mapa de Evidências",
        "Radar de Evidências",
        "Observatório de Qualidade",
    ):
        assert expected in advanced

    for forbidden in (
        "Evidence Engine",
        "Scientific Intelligence",
        "Human Synthesis Review",
        "Synthesis Brief",
        "Ask NutEV",
        "Workflow tipo Rayyan",
    ):
        assert forbidden not in advanced


def test_internal_compatibility_routes_remain_stable() -> None:
    ask = read_web("ask.js")
    context = read_web("ai-context.js")
    analysis = read_web("scientific-flow.js")

    assert "/api/agent-context/article1/status" in ask
    assert "/agent-context/article1/ARTICLE_SUMMARIES.jsonl" in ask
    assert "/api/agent-context/article1/status" in context
    assert "/agent-context/article1/SEARCH_STATE.json" in context
    assert "href:'/intelligence.html'" in analysis
    assert "href:'/review.html'" in analysis


def test_product_language_contract_explains_meaning_and_technical_exception() -> None:
    doc = DOC.read_text(encoding="utf-8")

    for expected in (
        "Sistema de Evidências Científicas",
        "Scientific Evidence System",
        "Consulta de Evidências",
        "Evidence Query",
        "Contexto de Evidências",
        "Evidence Context",
        "Análise de Evidências",
        "Evidence Analysis",
        "Nomear a função, não a tecnologia",
        "Exceção técnica interna",
        "AI_CONTEXT.md",
        "/api/agent-context/...",
    ):
        assert expected in doc


def test_scientific_tokens_remain_canonical() -> None:
    source = presentation_source() + "\n" + read_web("i18n.js")

    for canonical in ("PRESS", "GF-10", "PRISMA", "B-NORM", "C-STRUCT", "EvidenceClaim"):
        assert canonical in source


def test_legacy_product_names_exist_only_as_i18n_compatibility_aliases_or_declared_debt() -> None:
    i18n = read_web("i18n.js")

    for legacy in (
        "Evidence Engine",
        "Scientific Intelligence",
        "Ask NutEV",
        "AI Context",
        "retrieval grounded",
        "finding-ready",
        "fail-closed",
    ):
        assert legacy in i18n

    source = presentation_source()
    for legacy in ("Ask NutEV", "AI Context", "retrieval grounded"):
        assert legacy not in source
