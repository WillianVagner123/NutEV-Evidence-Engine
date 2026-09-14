from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_i18n_defaults_to_portuguese_and_persists_explicit_choice() -> None:
    script = read("i18n.js")

    assert "DEFAULT_LANGUAGE='pt-BR'" in script
    assert "ENGLISH_LANGUAGE='en'" in script
    assert "STORAGE_KEY='nutev_language'" in script
    assert "localStorage.setItem(STORAGE_KEY,currentLanguage)" in script
    assert "new URLSearchParams(location.search).get('lang')" in script
    assert "document.documentElement.lang" in script


def test_language_switch_is_native_accessible_and_responsive() -> None:
    script = read("i18n.js")
    css = read("i18n.css")

    assert "nutevLanguageSwitch" in script
    assert 'data-nutev-language="pt-BR"' in script
    assert 'data-nutev-language="en"' in script
    assert "aria-pressed" in script
    assert "setAttribute('role','group')" in script
    assert "nutev-language-switch-floating" in script
    assert ":focus-visible" in css
    assert "@media (max-width:700px)" in css
    assert ":has(" not in css


def test_i18n_is_ui_only_and_protects_scientific_source_content() -> None:
    script = read("i18n.js")

    for forbidden in (
        "fetch(",
        "XMLHttpRequest",
        "method:'POST'",
        'method:"POST"',
        "/api/",
        "sessionStorage",
    ):
        assert forbidden not in script

    for protected in (
        ".article-title",
        "[data-article-title]",
        ".abstract",
        "[data-abstract]",
        ".finding-excerpt",
        "[data-finding-excerpt]",
        "[data-raw-enum]",
        "blockquote",
        "cite",
    ):
        assert protected in script

    assert "data-article-title" in read("evidence.js")
    assert "data-article-title" in read("review-routes.js")
    assert "data-nutev-no-translate" in read("review-routes.js")


def test_bilingual_bootstrap_covers_product_ui_without_touching_session_lease() -> None:
    assert "i18n" not in read("tenant-session.js")
    assert "i18n.js" in read("product-ui.js")
    assert "i18n.js" in read("login.js")

    for name in (
        "scientific-flow.js",
        "operational-cycle.js",
        "synthesis-flow.js",
        "dashboard-visual.js",
        "strategy-flow-sync.js",
        "evidence.js",
        "review-routes.js",
    ):
        assert "i18n.js" in read(name)


def test_mixed_legacy_ui_has_portuguese_aliases_and_preserves_canonical_tokens() -> None:
    script = read("i18n.js")

    for expected in (
        "retrieval grounded",
        "result bundles",
        "workspace",
        "Providers / Watch",
        "Query freeze",
        "Full-text coverage",
        "finding-ready",
        "rank-blind",
        "fail-closed",
        "evidence-quality score",
        "canonical synthesis",
    ):
        assert expected in script

    # These tokens remain part of the product/scientific contract rather than
    # being replaced by translated aliases in the i18n registry.
    product_sources = "\n".join(
        read(name)
        for name in (
            "scientific-flow.js",
            "operational-cycle.js",
            "synthesis-flow.js",
            "evidence.js",
            "review-routes.js",
        )
    )
    for canonical in ("PRESS", "GF-10", "PRISMA", "B-NORM", "C-STRUCT", "EvidenceClaim"):
        assert canonical in product_sources or canonical in script


def test_alias_registry_and_dynamic_content_are_supported() -> None:
    script = read("i18n.js")

    assert "for(const [pt,en,aliases=[]] of PAIRS)" in script
    assert "for(const alias of aliases)EXACT.set(alias,entry)" in script
    assert "MutationObserver" in script
    assert "mutation.addedNodes" in script
    assert "nutev:language-change" in script
