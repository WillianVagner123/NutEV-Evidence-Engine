from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_search_page_loads_guided_recovery_after_resilient_search_events() -> None:
    html = read("search.html")

    assert "search-recovery.css" in html
    assert 'id="queryAssist"' in html
    assert 'id="searchRecovery"' in html
    assert "search-guided-recovery.js" in html
    assert html.index("search-events.js") < html.index("search-ux-resilience.js") < html.index("search-guided-recovery.js") < html.index("app.js")


def test_query_lint_warns_without_silently_rewriting_scientific_terms() -> None:
    recovery = read("search-guided-recovery.js")

    assert "unbalanced_quotes" in recovery
    assert "unbalanced_parentheses" in recovery
    assert "complex_boolean" in recovery
    assert "very_short" in recovery
    assert "long_quick_query" in recovery
    assert "não vai corrigi-los automaticamente" in recovery
    assert "Não adiciona sinônimos, descritores MeSH/DeCS ou termos científicos sem sua ação." in recovery
    assert "$('#question').value=" not in recovery


def test_low_or_zero_results_get_recovery_actions_not_scientific_conclusions() -> None:
    recovery = read("search-guided-recovery.js")

    assert "if(count>5)return null" in recovery
    assert "A busca terminou sem referências retornadas." in recovery
    assert "Isso descreve somente esta recuperação nas fontes consultadas e não prova ausência de evidência." in recovery
    assert "O conjunto é pequeno, mas o NutEV não interpreta isso como evidência insuficiente." in recovery
    for action in (
        "Revisar consulta",
        "Revisar fontes",
        "Tentar mesma pergunta com cobertura máxima",
        "Configurar Busca avançada",
        "Ver Minhas buscas",
    ):
        assert action in recovery


def test_provider_gaps_are_explained_before_query_broadening() -> None:
    recovery = read("search-guided-recovery.js")

    for field in ("failed_providers", "unavailable_providers", "non_exhaustive_providers"):
        assert field in recovery
    assert "Antes de mudar a pergunta, confira as fontes." in recovery
    assert "a lacuna não deve ser reinterpretada como ausência de evidência" in recovery


def test_recovery_actions_require_explicit_user_clicks() -> None:
    recovery = read("search-guided-recovery.js")

    assert "[data-recovery=\"global\"]" in recovery
    assert "addEventListener('click',()=>$('#globalSearchBtn')?.click())" in recovery
    assert "[data-recovery=\"advanced\"]" in recovery
    assert "addEventListener('click',()=>activateMode('advanced'))" in recovery
    assert "window.fetch=" not in recovery


def test_search_lifecycle_events_reduce_fetch_wrapper_coupling() -> None:
    events = read("search-events.js")
    ux = read("search-ux-resilience.js")
    recovery = read("search-guided-recovery.js")

    assert "emit('nutev:search-job'" in events
    assert "emit('nutev:search-result'" in events
    assert "emit('nutev:search-failed'" in events
    assert "getLastResult:()=>lastResult" in events
    assert "addEventListener('nutev:search-result'" in ux
    assert "addEventListener('nutev:search-result'" in recovery
    assert "addEventListener('nutev:search-job'" in recovery


def test_guided_recovery_does_not_restore_review_workflows_to_public_search() -> None:
    html = read("search.html")
    recovery = read("search-guided-recovery.js").casefold()

    assert "PRESS" not in html
    assert "PRISMA" not in html
    for forbidden in ("grade", "risk of bias", "recomendação clínica", "elegível para revisão"):
        assert forbidden not in recovery
