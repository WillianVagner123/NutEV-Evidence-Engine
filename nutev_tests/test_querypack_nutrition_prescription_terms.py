from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path("config/keyword_taxonomy.json"))


def test_semantic_terms_include_nutrition_prescription_variants() -> None:
    terms = semantic_terms("busca2b", min_priority=5)

    for term in [
        "nutrition prescription",
        "dietary prescription",
        "therapeutic diet prescription",
        "individualized nutrition prescription",
        "nutrition prescription protocol",
    ]:
        assert term in terms


def test_provider_queries_surface_nutrition_prescription_variants() -> None:
    queries = render_queries_for_provider(_taxonomy(), "busca2b", "openalex")
    joined_queries = " ".join(queries).lower()

    for term in [
        "nutrition prescription",
        "dietary prescription",
        "nutrition prescription protocol",
    ]:
        assert term in joined_queries
