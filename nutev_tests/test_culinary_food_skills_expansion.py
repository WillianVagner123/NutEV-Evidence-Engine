from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.settings import load_json


def test_artigo3_semantic_terms_include_culinary_food_skills_programs() -> None:
    terms = "\n".join(semantic_terms("artigo3_framework", min_priority=4)).lower()

    assert "culinary medicine curriculum" in terms
    assert "teaching kitchen program" in terms
    assert "kitchen-based intervention" in terms
    assert "food resource management intervention" in terms


def test_busca1_pubmed_queries_include_culinary_food_skills_variants() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca1", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "culinary medicine curriculum" in rendered
    assert "teaching kitchen program" in rendered
    assert "meal planning intervention" in rendered


def test_busca2b_crossref_queries_anchor_food_skills_to_clinical_scope() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "crossref")
    matching_queries = [
        query.lower()
        for query in queries
        if "food skills intervention" in query.lower()
    ]

    assert matching_queries
    assert any(
        "obesity" in query
        or "type 2 diabetes" in query
        or "cardiometabolic" in query
        or "masld" in query
        for query in matching_queries
    )
