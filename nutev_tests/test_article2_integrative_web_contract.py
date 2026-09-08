from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"
API = WEB / "article2_integrative_api.py"
ROUTES = WEB / "tenant_platform_routes.py"
ASSEMBLY = ROOT / "src" / "nutev" / "applications" / "willian_doctorate_a2" / "integrative.py"
A1_ASSEMBLY = ROOT / "src" / "nutev" / "applications" / "willian_doctorate_a1" / "d132.py"


def test_article2_api_requires_integrative_first_party_application_context() -> None:
    source = API.read_text(encoding="utf-8")
    assert 'ASSEMBLY_ID = "WILLIAN_DOCTORATE_A2"' in source
    assert 'descriptor.get("template_id") != INTEGRATIVE_REVIEW' in source
    assert 'configuration.get("assembly_id") != ASSEMBLY_ID' in source
    assert 'configuration.get("integrative_config_version") != _service().config().config_version' in source
    assert "_project_context(handler)" in source


def test_http_surface_cannot_activate_or_supply_legacy_binding() -> None:
    source = API.read_text(encoding="utf-8").casefold()
    assert "/api/article2/integrative/bootstrap" in source
    assert "/api/article2/integrative/status" in source
    assert "/api/article2/integrative/events" in source
    assert "/api/article2/integrative/advance" in source
    for forbidden_route in (
        "/api/article2/integrative/bind",
        "/api/article2/integrative/legacy-binding",
        "/api/article2/integrative/activate",
        "/api/article2/integrative/migrate",
    ):
        assert forbidden_route not in source
    assert "legacybindingevidence" not in source
    assert "register_legacy_binding" not in source
    assert "source_path" not in source
    assert "file_path" not in source
    assert "busca2a" not in source
    assert "busca2b" not in source


def test_http_advance_body_carries_only_transition_evidence_not_tenant_identity() -> None:
    source = API.read_text(encoding="utf-8")
    assert 'body.get("next_phase")' in source
    assert 'body.get("evidence")' in source
    assert 'body.get("workspace_id")' not in source
    assert 'body.get("project_id")' not in source
    assert 'body.get("application_id")' not in source
    assert 'body.get("search_id")' not in source
    assert 'body.get("query")' not in source


def test_article2_assembly_reuses_platform_primitives_without_copying_article1_or_search_engine() -> None:
    source = ASSEMBLY.read_text(encoding="utf-8")
    lowered = source.casefold()
    assert "from nutev.tenancy import" in source
    assert "PermissionService" in source
    assert "AuthorizationContext" in source
    assert "willian_doctorate_a1" not in lowered
    assert "article1_d132" not in lowered
    assert "from nutev.search" not in lowered
    assert "import nutev.search" not in lowered
    assert "http" not in {line.strip().split()[1] for line in source.splitlines() if line.strip().startswith("import ") and len(line.strip().split()) > 1}

    # A1 and A2 are separate assemblies, not files copied from one another.
    a1 = A1_ASSEMBLY.read_text(encoding="utf-8")
    assert source != a1


def test_tenant_platform_installs_article2_as_an_application_extension() -> None:
    routes = ROUTES.read_text(encoding="utf-8")
    assert "from article2_integrative_api import install_article2_integrative_routes" in routes
    assert "install_article2_integrative_routes()" in routes


def test_article2_runtime_does_not_treat_historical_workstream_names_as_ownership() -> None:
    source = ASSEMBLY.read_text(encoding="utf-8").casefold()
    assert "busca2a" not in source
    assert "busca2b" not in source
    assert "current_login" not in source
    assert "search_id" not in source
