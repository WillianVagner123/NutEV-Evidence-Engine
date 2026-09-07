from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_public_search_has_inline_feedback_progress_and_keyboard_flow() -> None:
    html = read("search.html")
    ux = read("search-ux-resilience.js")

    assert "search-ux.css" in html
    assert 'id="searchFeedback"' in html
    assert 'role="alert"' in html
    assert 'id="searchProgress"' in html
    assert 'aria-live="polite"' in html
    assert "search-ux-resilience.js" in html
    assert html.index("search-facets-ui.js") < html.index("search-ux-resilience.js") < html.index("app.js")
    assert "window.alert=message=>" in ux
    assert "event.ctrlKey||event.metaKey" in ux
    assert "history.replaceState" in ux


def test_job_polling_retries_only_safe_status_reads_not_search_submission() -> None:
    ux = read("search-ux-resilience.js")

    assert "const isJobRead=method==='GET'&&path.startsWith('/api/search/jobs/')" in ux
    assert "isJobRead?await robustJobFetch(args):await previousFetch(...args)" in ux
    assert "RETRY_DELAYS=[400,900,1800]" in ux
    assert "sem repetir a busca" in ux
    assert "method==='POST'" in ux


def test_search_outcome_distinguishes_partial_coverage_from_scientific_quality() -> None:
    ux = read("search-ux-resilience.js")

    assert "Busca concluída com cobertura parcial" in ux
    assert "Busca concluída sem resultados retornados" in ux
    assert "Isso não prova ausência de evidência" in ux
    assert "Cobertura descreve recuperação das fontes, não qualidade, certeza ou elegibilidade da evidência." in ux
    assert "failed_providers" in ux
    assert "unavailable_providers" in ux
    assert "non_exhaustive_providers" in ux


def test_technical_audit_is_collapsed_but_audit_errors_are_not_hidden() -> None:
    ux = read("search-ux-resilience.js")

    assert "details.plan-audit" in ux
    assert "removeAttribute('open')" in ux
    assert "Detalhes técnicos da busca" in ux
    assert "node.matches?.('.review-result-note')||node.matches?.('.warning')" in ux
    assert "node.matches?.('.error')" not in ux


def test_result_cards_keep_explanations_visible_and_collapse_long_secondary_content() -> None:
    ux = read("search-ux-resilience.js")
    facets = read("search-facets-ui.js")

    assert "Ver resumo do artigo" in ux
    assert "Como foi classificado" in ux
    assert "why-match" in facets
    assert "Por que foi recuperado" in facets
    assert "Sinais do ranking final" in facets
    assert "Confiança da classificação" in facets


def test_result_refinement_supports_local_text_search_and_visible_active_filters() -> None:
    facets = read("search-facets-ui.js")
    css = read("search-facets.css")

    assert "facetText" in facets
    assert "Buscar nestes resultados" in facets
    assert "searchableText(record)" in facets
    assert "activeResultFilters" in facets
    assert "filtros ativos" in facets
    assert "sem refazer a busca nas fontes" in facets
    assert ".facet-chip" in css
    assert ".facet-text-search" in css


def test_search_ux_does_not_add_scientific_authority_or_review_workflow_to_public_flow() -> None:
    ux = read("search-ux-resilience.js").casefold()
    html = read("search.html")

    for forbidden in (
        "grade",
        "risk of bias",
        "certeza da evidência",
        "recomendação clínica",
        "elegível para revisão",
    ):
        assert forbidden not in ux
    assert "PRESS" not in html
    assert "PRISMA" not in html
