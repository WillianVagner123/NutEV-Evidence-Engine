from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def test_saved_library_keeps_legacy_local_store_and_pilot_private_placements_separate_from_workbench() -> None:
    store = (WEB / "saved-library.js").read_text(encoding="utf-8")
    workbench = (WEB / "article_workbench_data.py").read_text(encoding="utf-8")
    server = (WEB / "server.py").read_text(encoding="utf-8")

    assert "indexedDB.open" in store
    assert "canonicalSavedKey" in store
    assert "doi:" in store
    assert "pmid:" in store
    assert "url:" in store
    assert "browser_saved_search_result_not_scientific_inclusion" in store
    assert "server_private_placement_not_scientific_inclusion" in store
    assert "/api/auth/status" in store
    assert "/api/library?scope=${scope}&limit=500" in store
    assert "/api/library/placements" in store
    assert "function serverScope(current){return current?.project_id?'project':'workspace'}" in store
    assert "mode=ro" in workbench
    assert 'path == "/api/articles"' in server
    assert '"/api/library"' not in server  # tenant routes are installed by the secure extension, not the legacy base server


def test_search_can_save_single_open_tenant_library_and_save_all() -> None:
    html = (WEB / "search.html").read_text(encoding="utf-8")
    ui = (WEB / "search-library-ui.js").read_text(encoding="utf-8")

    assert html.index("search-library-ui.js") < html.index("app.js")
    assert "Cobertura máxima disponível" in html
    assert "Guardar na Biblioteca" in ui
    assert "Guardar todos os resultados retornados" in ui
    assert "Abrir na Biblioteca" in ui
    assert "Abrir dossiê" in ui  # legacy compatibility label
    assert "saveArticle(" in ui
    assert "saveArticles(" in ui
    assert "'/evidence-library.html'" in ui
    assert "/articles.html?saved=" in ui  # legacy compatibility route
    assert "existing?.dataset.savedLibraryKey!==key" in ui
    assert "existing?.remove()" in ui
    assert "outcome.scope==='project'" in ui


def test_saved_snapshot_keeps_all_observed_sources_and_manifestations() -> None:
    store = (WEB / "saved-library.js").read_text(encoding="utf-8")

    assert "sourceProvidersFor(record)" in store
    assert "sourceManifestationsFor(record)" in store
    assert "source_providers:sourceProvidersFor(record)" in store
    assert "source_manifestations:sourceManifestationsFor(record)" in store
    assert "...(item.source_providers||[])" in store
    assert "...(p.source_providers||[])" in store


def test_legacy_biblioteca_surfaces_saved_core_without_replacing_verified_corpus() -> None:
    html = (WEB / "articles.html").read_text(encoding="utf-8")
    ui = (WEB / "saved-library-ui.js").read_text(encoding="utf-8")
    css = (WEB / "saved-library.css").read_text(encoding="utf-8")

    assert "saved-library.css" in html
    assert "saved-library-ui.js" in html
    assert "corpus científico verificado" in html
    assert "Meus salvos" in ui
    assert "Persistem neste navegador" in ui
    assert "Origens antes da deduplicação" in ui
    assert "Proveniência das buscas" in ui
    assert "Múltiplas fontes significam múltiplas manifestações recuperadas" in ui
    assert "Não equivale a inclusão em revisão" in ui
    assert ".saved-core" in css
    assert ".saved-source-list" in css
