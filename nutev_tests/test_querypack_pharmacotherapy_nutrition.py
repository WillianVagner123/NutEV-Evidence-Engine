from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path("config/keyword_taxonomy.json"))


def test_busca2b_components_include_pharmacotherapy_nutrition_terms() -> None:
    _, components = build_structured_components(_taxonomy(), "busca2b")
    focus_terms = {term.lower() for term in components["focus_terms"]}

    assert "anti-obesity medication nutrition" in focus_terms
    assert "glp-1 receptor agonist nutrition care" in focus_terms
    assert "incretin therapy dietary counseling" in focus_terms
    assert "post-glp-1 weight maintenance" in focus_terms


def test_busca2b_provider_queries_surface_pharmacotherapy_nutrition_terms() -> None:
    queries = render_queries_for_provider(_taxonomy(), "busca2b", "pubmed")
    joined_queries = " ".join(queries).lower()

    assert "anti-obesity medication nutrition" in joined_queries
    assert "glp-1 receptor agonist nutrition care" in joined_queries
    assert "incretin therapy dietary counseling" in joined_queries
    assert "post-glp-1 weight maintenance" in joined_queries
    assert "obesity" in joined_queries or "type 2 diabetes" in joined_queries
