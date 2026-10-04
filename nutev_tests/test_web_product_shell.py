from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def html(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_every_sidebar_page_loads_the_shared_product_shell() -> None:
    missing: list[str] = []
    for page in sorted(WEB.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        if '<aside class="sidebar"' not in text:
            continue
        if 'src="./product-ui.js"' not in text and "src='/product-ui.js'" not in text:
            missing.append(page.name)
    assert not missing, f"sidebar pages missing product-ui.js: {missing}"


def test_product_shell_reuses_one_css_link_and_hides_build_metadata_by_default() -> None:
    js = (WEB / "product-ui.js").read_text(encoding="utf-8")
    assert "querySelectorAll('link[rel=\"stylesheet\"]')" in js
    assert "document.head.appendChild(existing)" in js
    assert "product-version-details" in js
    assert "Sobre esta versão" in js
    assert "footer.textContent=\`NutEV · build" not in js


def test_dashboard_shared_css_uses_the_canonical_minimal_tokens() -> None:
    css = (WEB / "dashboard.css").read_text(encoding="utf-8")
    assert "--dashboard-bg:#fafaf9" in css
    assert "--dashboard-radius:8px" in css
    assert ".metric-card::after{display:none}" in css
    assert "linear-gradient(180deg,#fff,#fbfcfb)" not in css


def test_primary_scientific_page_titles_are_task_language() -> None:
    expected = {
        "quality.html": "Qualidade do sistema",
        "claim-appraisal.html": "Avaliação de alegações",
        "evidence-claims.html": "Revisão de alegações",
        "evidence-sets.html": "Conjuntos de evidências",
        "recommendation-candidates.html": "Rascunhos de recomendação",
        "recommendation-human-validation.html": "Validação humana da recomendação",
        "recommendation-development.html": "Desenvolvimento da recomendação",
        "recommendation-adoption.html": "Adoção da recomendação",
        "synthesis-governance.html": "Governança da síntese",
        "synthesis-release.html": "Liberação governada da síntese",
        "synthesis-publication.html": "Manifesto de publicação",
    }
    for name, heading in expected.items():
        match = re.search(r"<h1[^>]*>(.*?)</h1>", html(name), flags=re.S)
        assert match, name
        rendered = re.sub(r"<[^>]+>", " ", match.group(1))
        rendered = " ".join(rendered.split())
        assert rendered == heading, (name, rendered)


def test_home_primary_actions_are_not_nested_cards() -> None:
    text = html("index.html")
    assert 'class="card home-action"' not in text
    assert text.count('class="home-action"') >= 4
