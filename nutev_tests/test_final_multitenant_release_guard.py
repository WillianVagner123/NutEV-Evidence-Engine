from __future__ import annotations

from pathlib import Path

from tools.check_runtime_http_surface import EXPECTED_PRIVATE_UNAUTHENTICATED_STATUS

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "apps" / "nutev-web" / "tenant_release_guard.py"
ROUTES = ROOT / "apps" / "nutev-web" / "tenant_platform_routes.py"
DEPLOY = ROOT / ".github" / "workflows" / "deploy-hetzner.yml"
RUNTIME_SMOKE = ROOT / "tools" / "check_runtime_http_surface.py"


def test_release_guard_fails_closed_workbench_and_article1_static_context() -> None:
    source = GUARD.read_text(encoding="utf-8")
    assert 'path == "/api/articles"' in source
    assert 'path.startswith("/api/articles/")' in source
    assert '"legacy_workbench_unavailable_in_pilot"' in source
    assert '"replacement": "/api/library"' in source
    assert 'path == "/agent-context/article1"' in source
    assert 'path.startswith("/agent-context/article1/")' in source
    assert "SCOPING_REVIEW" in source
    assert 'WILLIAN_DOCTORATE_A1' in source
    assert "unquote(urlparse(self.path).path)" in source


def test_release_guard_is_installed_after_application_routes() -> None:
    source = ROUTES.read_text(encoding="utf-8")
    guard_pos = source.index("install_tenant_release_guard()")
    assert guard_pos > source.index("install_library_routes()")
    assert guard_pos > source.index("install_application_routes()")
    assert guard_pos > source.index("install_export_audit_routes()")
    assert guard_pos > source.index("install_review_routes()")
    assert guard_pos > source.index("install_article1_d132_routes()")
    assert guard_pos > source.index("install_article2_integrative_routes")


def test_final_runtime_smoke_covers_required_private_surfaces() -> None:
    required = {
        "/api/auth/me": {401},
        "/api/context": {401},
        "/api/searches": {401},
        "/api/articles": {401},
        "/api/library": {401},
        "/api/review": {401},
        "/agent-context/article1/SEARCH_STATE.json": {401},
        "/api/article1/d132/review": {401},
        "/api/article2/integrative/status": {401, 404},
    }
    assert set(EXPECTED_PRIVATE_UNAUTHENTICATED_STATUS) == set(required)
    for path, statuses in required.items():
        assert EXPECTED_PRIVATE_UNAUTHENTICATED_STATUS[path] == frozenset(statuses)


def test_deploy_executes_runtime_smoke_before_and_after_promotion() -> None:
    source = DEPLOY.read_text(encoding="utf-8")
    assert source.count("python tools/check_runtime_http_surface.py") >= 2
    assert source.count('--expected-commit "$TARGET_SHA"') >= 2
    assert "preflight" in source
    assert "production" in source


def test_final_runtime_smoke_defaults_to_pilot_and_11_provider_contract() -> None:
    source = RUNTIME_SMOKE.read_text(encoding="utf-8")
    assert 'default="pilot"' in source
    assert 'expected_auth_mode: str = "pilot"' in source
    assert '"/api/auth/status"' in source
    assert '"/api/providers"' in source
    assert "EXPECTED_PROVIDER_IDS" in source
    assert "private_surfaces_unauthenticated" in source
