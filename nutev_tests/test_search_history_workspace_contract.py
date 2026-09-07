from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_history_workspace_is_wired_after_event_bus_and_before_app() -> None:
    html = read("search.html")

    assert "search-history.css" in html
    assert "search-history-ui.js" in html
    assert html.index("search-events.js") < html.index("search-history-ui.js") < html.index("app.js")


def test_history_consumes_existing_api_event_without_new_network_wrapper() -> None:
    events = read("search-events.js")
    history = read("search-history-ui.js")

    assert "path==='/api/searches'&&method==='GET'" in events
    assert "emit('nutev:search-history'" in events
    assert "getLastHistory:()=>[...lastHistory]" in events
    assert "addEventListener('nutev:search-history'" in history
    assert "window.fetch=" not in history
    assert "/api/searches" not in history


def test_history_exposes_query_status_counts_and_provider_gaps() -> None:
    history = read("search-history-ui.js")

    assert "Concluída com lacunas" in history
    assert "Concluída" in history
    assert "Falhou" in history
    assert "unique_records" in history
    assert "returned_records" in history
    assert "failed_providers" in history
    assert "unavailable_providers" in history
    assert "lacuna" in history
    assert "Abrir resultados" in history


def test_history_has_local_accent_insensitive_filter() -> None:
    history = read("search-history-ui.js")
    css = read("search-history.css")

    assert "normalize('NFD')" in history
    assert "historyFilter" in history
    assert "Buscar no histórico" in history
    assert "historySearch" in history
    assert "historyVisibleCount" in history
    assert ".history-filter" in css


def test_reusing_history_prepares_quick_search_but_never_runs_it() -> None:
    history = read("search-history-ui.js")

    assert "Usar pergunta em nova busca" in history
    assert "input[name=\"searchMode\"][value=\"quick\"]" in history
    assert "quick?.click()" in history
    assert "question.value=query" in history
    assert "a nova busca só começa quando você clicar" in history
    assert "searchParams.delete('view')" in history
    assert "searchParams.delete('q')" in history
    assert "history.replaceState" in history
    assert "question?.focus()" in history
    assert "#searchBtn" not in history
    assert "runSearch" not in history
    assert "/api/search/jobs" not in history


def test_history_does_not_claim_exact_rerun_or_scientific_authority() -> None:
    history = read("search-history-ui.js").casefold()

    for forbidden in (
        "repetir estratégia exata",
        "rerun exato",
        "grade",
        "risk of bias",
        "certeza da evidência",
        "recomendação clínica",
        "elegível para revisão",
    ):
        assert forbidden not in history
