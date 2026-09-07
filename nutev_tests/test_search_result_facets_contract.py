from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def test_search_loads_facets_before_main_renderer_and_keeps_library_bridge() -> None:
    html = (WEB / "search.html").read_text(encoding="utf-8")

    assert "search-facets.css" in html
    assert "search-facets-ui.js" in html
    assert html.index("search-library-ui.js") < html.index("search-facets-ui.js") < html.index("app.js")


def test_facets_cover_reliable_returned_result_dimensions() -> None:
    facets = (WEB / "search-facets-ui.js").read_text(encoding="utf-8")

    for control in ("facetYear", "facetClass", "facetProvider", "facetTaxonomy", "facetSort"):
        assert control in facets
    for sort_key in ("query_relevance", "final_score", "newest", "nutev_priority"):
        assert sort_key in facets
    assert "resultados retornados nesta busca" in facets
    assert "data-result-index" in facets


def test_provider_facet_counts_and_filters_every_observed_source_after_deduplication() -> None:
    facets = (WEB / "search-facets-ui.js").read_text(encoding="utf-8")

    assert "function providerValues(record)" in facets
    assert "record?.source_providers" in facets
    assert "countedMultiOptions(records,providerValues,providerLabel)" in facets
    assert "providerValues(record).includes(filters.provider)" in facets
    assert "Um artigo deduplicado pode contar em mais de uma fonte" in facets
    assert "proveniência de recuperação, não qualidade da evidência" in facets


def test_multi_source_results_expose_retrieval_origins_without_claiming_scientific_strength() -> None:
    facets = (WEB / "search-facets-ui.js").read_text(encoding="utf-8")
    css = (WEB / "search-facets.css").read_text(encoding="utf-8")

    assert "source_manifestations" in facets
    assert "Origens da recuperação" in facets
    assert "provider_query" in facets
    assert "Múltiplas fontes não aumentam qualidade, certeza ou elegibilidade científica." in facets
    assert "multi-source-pill" in facets
    assert ".retrieval-provenance" in css


def test_facet_sorting_does_not_break_saved_article_identity() -> None:
    facets = (WEB / "search-facets-ui.js").read_text(encoding="utf-8")
    library = (WEB / "search-library-ui.js").read_text(encoding="utf-8")

    assert 'data-result-index="${entry.index}"' in facets
    assert "card.dataset.resultIndex" in library
    assert "results[resultIndex]" in library
    assert "canonicalSavedKey(record)" in library


def test_facets_hide_while_new_search_is_loading() -> None:
    facets = (WEB / "search-facets-ui.js").read_text(encoding="utf-8")

    assert "summary.classList.contains('hidden')" in facets
    assert "existingWorkspace?.classList.add('hidden')" in facets
    assert "workspace.classList.remove('hidden')" in facets


def test_facets_are_client_side_refinement_not_new_scientific_authority() -> None:
    facets = (WEB / "search-facets-ui.js").read_text(encoding="utf-8")
    server = (WEB / "server.py").read_text(encoding="utf-8")

    assert "sem refazer a busca nas fontes" in facets
    assert "reference_score" in facets
    assert "query_relevance_score" in facets
    assert "nutev_priority_score" in facets
    assert "/api/facets" not in server
