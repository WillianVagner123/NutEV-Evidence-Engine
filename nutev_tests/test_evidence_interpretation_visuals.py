from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_visual_layer_is_wired_to_all_three_surfaces() -> None:
    for page in ("evidence-map.html", "intelligence.html", "review.html"):
        assert './evidence-interpretation.js' in read(page)

    script = read("evidence-interpretation.js")
    assert "Structure → Inspect → Human review" in script
    assert "/evidence-map.html" in script
    assert "/intelligence.html" in script
    assert "/review.html" in script


def test_visual_layer_is_dom_derived_and_does_not_create_a_parallel_data_path() -> None:
    script = read("evidence-interpretation.js")

    for forbidden in (
        "fetch(",
        "XMLHttpRequest",
        "/api/",
        "localStorage",
        "sessionStorage",
        "ARTICLE_SUMMARIES.jsonl",
    ):
        assert forbidden not in script

    assert "MutationObserver" in script
    assert "INTERPRETATION WORKFLOW · NAVIGATION ONLY" in script


def test_interpretation_rail_keeps_current_surface_non_link() -> None:
    script = read("evidence-interpretation.js")

    assert '<span class="ei-stage active" aria-current="page">' in script
    assert '<a class="ei-stage" href="${href}">' in script
    assert "return key===page" in script


def test_evidence_map_visual_delegates_to_existing_domain_filter() -> None:
    script = read("evidence-interpretation.js")

    assert "#evidenceMatrix tbody tr" in script
    assert ".matrix-cell[data-domain]" in script
    assert "#mapDomainFilter" in script
    assert "dispatchEvent(new Event('change',{bubbles:true}))" in script
    assert "volume ≠ strength" in script
    assert "célula vazia não representam qualidade, certeza, ausência de literatura ou evidence gap" in script


def test_intelligence_visual_delegates_to_existing_domain_selection() -> None:
    script = read("evidence-interpretation.js")

    assert "[data-domain-card]" in script
    assert "[data-select-domain]" in script
    assert "target?.click()" in script
    assert "finding-ready ≠ accepted claim" in script
    assert "Finding-ready descreve disponibilidade técnica de result bundle" in script
    assert "Não significa força, convergência, certeza, elegibilidade nem EvidenceClaim aceito" in script


def test_review_visual_reports_submission_progress_without_scientific_inference() -> None:
    script = read("evidence-interpretation.js")

    assert ".review-round-card" in script
    assert ".open-review" in script
    assert ".round-details" in script
    assert "revisores enviaram e travaram a própria avaliação" in script
    assert "A barra mede somente submissão humana registrada" in script
    assert "não calcula inclusão, concordância, adjudicação científica, risco de viés, certeza ou PRISMA" in script

    for forbidden in (
        "createReviewRound",
        "submitReview",
        "saveAssignment",
        "method:'POST'",
        'method:"POST"',
        "/api/review",
    ):
        assert forbidden not in script


def test_visual_controls_are_keyboard_native_and_responsive() -> None:
    script = read("evidence-interpretation.js")
    css = read("evidence-interpretation.css")

    assert 'type="button"' in script
    assert "aria-pressed" in script
    assert "aria-current" in script
    assert ":focus-visible" in css
    assert "@media(max-width:900px)" in css
    assert "@media(max-width:560px)" in css
