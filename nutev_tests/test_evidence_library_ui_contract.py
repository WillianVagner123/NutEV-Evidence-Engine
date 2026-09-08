from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def test_pilot_evidence_library_page_is_server_backed() -> None:
    html = (WEB / "evidence-library.html").read_text(encoding="utf-8")
    script = (WEB / "evidence-library-page.js").read_text(encoding="utf-8")

    assert "Evidence Library" in html
    assert "evidence-library-page.js" in html
    assert "/api/context" in script
    assert "/api/library?scope=" in script
    assert "/api/library/placements" in script
    assert "/api/library/full-text/" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "indexedDB" not in script


def test_hybrid_facade_never_falls_back_to_indexeddb_in_pilot_mode() -> None:
    script = (WEB / "evidence-library-bootstrap.js").read_text(encoding="utf-8")

    assert "if(state.mode==='legacy')return legacy.list()" in script
    assert "if(state.mode==='legacy')return legacy.save(record)" in script
    assert "if(state.mode==='legacy')return legacy.remove(id)" in script
    assert "if(!state.context)throw new Error('workspace_context_required')" in script
    assert "/api/library/placements" in script
    assert "window.NutEVEvidenceLibrary=facade" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script


def test_pilot_library_does_not_claim_indexeddb_ownership_migration() -> None:
    docs = (ROOT / "docs" / "MULTITENANT_EVIDENCE_LIBRARY.md").read_text(encoding="utf-8")
    assert "historical IndexedDB items → no automatic migration" in docs
    assert "does not prove" in docs
    assert "which workspace owns it" in docs
    assert "which project owns it" in docs


def test_full_text_ui_contract_never_mentions_internal_cache_path() -> None:
    page = (WEB / "evidence-library-page.js").read_text(encoding="utf-8")
    api = (WEB / "tenant_library_api.py").read_text(encoding="utf-8")

    assert "cache_path_exposed" in api
    assert '"cache_path_exposed": False' in api
    assert "cache_path" not in page
    assert "storage_path" not in page
