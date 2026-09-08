from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def test_pilot_evidence_library_page_is_server_backed() -> None:
    html = (WEB / "evidence-library.html").read_text(encoding="utf-8")
    script = (WEB / "evidence-library-page.js").read_text(encoding="utf-8")

    assert "Biblioteca de evidências" in html
    assert "evidence-library-page.js" in html
    assert "/api/context" in script
    assert "/api/library?scope=" in script
    assert "/api/library/placements" in script
    assert "/api/library/full-text/" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "indexedDB" not in script


def test_real_saved_library_module_routes_pilot_to_selected_server_scope_without_silent_local_fallback() -> None:
    store = (WEB / "saved-library.js").read_text(encoding="utf-8")
    bootstrap = (WEB / "evidence-library-bootstrap.js").read_text(encoding="utf-8")

    assert "/api/auth/status" in store
    assert "if(!response.ok)throw new Error(`auth_status_http_${response.status}`)" in store
    assert "if(mode==='pilot')return serverSaveArticles(records)" in store
    assert "if(mode==='pilot')return filterRows(await serverLibraryRows(),q,limit)" in store
    assert "function serverScope(current){return current?.project_id?'project':'workspace'}" in store
    assert "/api/library?scope=${scope}&limit=500" in store
    assert "/api/library/placements" in store
    assert "body:JSON.stringify({article_id:articleId,scope,state:'not_screened'" in store
    assert "global_article_id_required" in store
    assert "indexedDB.open" in store
    assert "localStorage" not in store
    assert "sessionStorage" not in store
    assert "import * as library from './saved-library.js'" in bootstrap
    assert "window.NutEVEvidenceLibrary=library" in bootstrap


def test_pilot_library_does_not_claim_indexeddb_ownership_migration() -> None:
    docs = (ROOT / "docs" / "MULTITENANT_EVIDENCE_LIBRARY.md").read_text(encoding="utf-8")
    assert "historical IndexedDB items → no automatic migration" in docs
    assert "does not prove" in docs
    assert "which workspace owns it" in docs
    assert "which project owns it" in docs


def test_full_text_ui_contract_never_mentions_internal_cache_path() -> None:
    page = (WEB / "evidence-library-page.js").read_text(encoding="utf-8")
    api = (WEB / "tenant_library_api.py").read_text(encoding="utf-8")

    assert "cache_path_exposed" not in api
    assert '"cache_path"' not in api
    assert '"storage_path"' not in api
    assert "cache_path" not in page
    assert "storage_path" not in page
