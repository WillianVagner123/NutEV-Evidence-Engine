from pathlib import Path

from nutev.querypacks.builders import build_queries, build_structured_components
from nutev.settings import load_json


def test_nutrition_referral_terms_expand_busca2b_query_components() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    _, components = build_structured_components(taxonomy, "busca2b")

    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}
    doc_terms = {term.lower() for term in components["doc_type_terms"]}

    assert "nutrition referral" in focus_terms
    assert "dietitian referral" in focus_terms
    assert "primary care nutrition referral" in web_hints
    assert "team-based nutrition care implementation" in web_hints
    assert "referral pathway" in doc_terms


def test_nutrition_referral_terms_render_in_busca2b_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    rendered = " ".join(build_queries(taxonomy, "busca2b")).lower()

    assert "nutrition referral" in rendered
    assert "dietitian referral" in rendered
    assert "primary care nutrition referral" in rendered
    assert "team-based nutrition care implementation" in rendered
