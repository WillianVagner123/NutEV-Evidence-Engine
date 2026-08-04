from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path("config/keyword_taxonomy.json"))


def test_glp1_nutrition_terms_prioritize_cardiometabolic_workstreams() -> None:
    busca2a_terms = {term.lower() for term in semantic_terms("busca2a", min_priority=4)}
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}
    busca1_terms = {term.lower() for term in semantic_terms("busca1", min_priority=4)}

    expected_terms = {
        "glp-1 nutrition",
        "glp-1 receptor agonist dietary counseling",
        "anti-obesity medication nutrition care",
        "obesity pharmacotherapy dietary adherence",
        "incretin therapy medical nutrition therapy",
        "muscle preservation during weight loss",
        "protein intake during weight loss",
    }

    assert expected_terms.issubset(busca2a_terms)
    assert expected_terms.issubset(busca2b_terms)
    assert "glp-1 nutrition" not in busca1_terms


def test_busca2_provider_queries_surface_glp1_nutrition_care_terms() -> None:
    queries = render_queries_for_provider(_taxonomy(), "busca2b", "openalex")
    joined_queries = " ".join(queries).lower()

    assert "glp-1 nutrition" in joined_queries
    assert "anti-obesity medication nutrition" in joined_queries
    assert "incretin therapy nutrition care" in joined_queries
    assert "protein intake during weight loss" in joined_queries
