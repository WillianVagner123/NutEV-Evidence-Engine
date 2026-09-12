from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_review_control_center_is_fail_closed() -> None:
    html = read("review.html")
    script = read("review-control.js")

    assert "ResearchApplication" in html
    assert "Rounds sem binding explícito" in html
    assert "O Review genérico não importa rounds antigos por inferência" in script
    assert "review_application_required" in script
    assert "applicationPayload.application||null" in script


def test_review_control_is_application_scoped_not_article1_reading_workspace() -> None:
    html = read("review.html")
    script = read("review-control.js")

    assert "Somente rounds explicitamente vinculados à ResearchApplication ativa" in html
    assert "workspace, projeto e aplicação" in html
    assert "jsonFetch('/api/application')" in script
    assert "jsonFetch('/api/review')" in script
    assert "/agent-context/article1" not in script
    assert "/api/article1/" not in script
    assert "SEARCH_STATE.json" not in script
    assert "ARTICLE_SUMMARIES.jsonl" not in script


def test_review_control_requires_explicit_human_decisions_and_never_auto_promotes_science() -> None:
    html = read("review.html")
    script = read("review-control.js")

    assert "Seleção científica automática" in html
    assert "Não existe." in html
    assert "PRISMA automático" in html
    assert "Nenhuma decisão humana é criada, inferida ou promovida automaticamente" in html
    assert "/api/review/decision" in script
    assert "/api/review/submit" in script
    assert "method:'POST'" in script
    assert "saveAssignment" in script
    assert "submitReview" in script


def test_primary_product_surfaces_expose_generic_review_control() -> None:
    project = read("project-page.js")
    context = read("workspace-context.js")

    assert "href:'/review.html'" in project
    assert "Rounds isolados por aplicação" in project
    assert "'/review.html'" in context
    assert "promoteReviewNavigation" in context
