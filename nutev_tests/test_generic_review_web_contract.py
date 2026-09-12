from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def text(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_review_page_is_generic_application_scoped_and_not_article1_bound() -> None:
    page = text("review.html")
    script = text("review-control.js")

    assert "/tenant-session.js" in page
    assert "./product-ui.js" in page
    assert "./workspace-context.js" in page
    assert "./review-control.js" in page
    assert "ResearchApplication" in page
    assert "Rounds sem binding explícito" in page

    assert "jsonFetch('/api/review')" in script
    assert "jsonFetch('/api/application')" in script
    assert "/api/review/rounds/" in script
    assert "/api/review/decision" in script
    assert "/api/review/submit" in script
    assert "/agent-context/article1" not in script
    assert "/api/article1/" not in script
    assert "D-132" not in script


def test_generic_review_routes_are_installed_before_release_guard() -> None:
    routes = text("tenant_platform_routes.py")
    api = text("tenant_review_api.py")

    assert "from tenant_review_api import install_review_routes" in routes
    assert "install_review_routes()" in routes
    assert routes.index("install_review_routes()") < routes.index("install_tenant_release_guard()")
    assert '"/api/review/rounds"' in api
    assert '"/api/review/decision"' in api
    assert '"/api/review/submit"' in api
    assert 'parsed.path == "/api/review"' in api
    assert "ApplicationScopedReviewService" in api


def test_review_is_promoted_only_on_authenticated_project_navigation() -> None:
    context = text("workspace-context.js")
    project = text("project-page.js")

    assert "'/review.html'" in context
    assert "promoteReviewNavigation" in context
    assert 'link.href=\'/review.html\'' in context
    assert "data.nutevReviewNav" not in context  # dataset is written as a property, not HTML data plumbing.
    assert "href:'/review.html'" in project
    assert "Rounds isolados por aplicação" in project
    assert "href:'/advanced.html#reviews'" not in project


def test_generic_review_copy_preserves_human_decision_guardrails() -> None:
    page = text("review.html")
    script = text("review-control.js")

    assert "Nenhuma decisão humana é criada, inferida ou promovida automaticamente" in page
    assert "Seleção científica automática" in page
    assert "PRISMA automático" in page
    assert "O Review genérico não importa rounds antigos por inferência" in script
