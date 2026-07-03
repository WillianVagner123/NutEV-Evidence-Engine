from __future__ import annotations

from nutev.querypacks.builders import build_queries
from nutev.querypacks.semantic_blocks import semantic_terms


def _taxonomy_with_broad_lifestyle_focus() -> dict:
    return {
        "global": {
            "lifestyle_medicine_pillars": {
                "nutrition": [
                    "nutrition",
                    "medical nutrition therapy",
                    "healthy eating",
                ]
            },
            "diet_patterns": {
                "core": ["dietary pattern", "healthy diet"]
            },
            "nutrition_domains": {
                "core": ["food literacy", "meal planning"]
            },
            "implementation_behavior": {
                "core": ["implementation"]
            },
            "document_types": {
                "reviews": ["systematic review"]
            },
        },
        "clinical": {
            "obesity": ["obesity"]
        },
        "outcomes": {
            "cardiometabolic": ["cardiometabolic risk"]
        },
        "workstreams": {
            "busca2b": {
                "population_terms": ["adults"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "priority_outcomes": ["cardiometabolic"],
                "document_type_keys": ["reviews"],
                "focus_blocks": ["lifestyle_medicine_pillars"],
                "web_query_hints": [],
            }
        },
    }


def test_broad_lifestyle_queries_keep_nutrition_anchor() -> None:
    queries = build_queries(_taxonomy_with_broad_lifestyle_focus(), "busca2b")

    broad_lifestyle_queries = [
        query
        for query in queries
        if '"lifestyle intervention"' in query or '"lifestyle medicine"' in query
    ]

    assert broad_lifestyle_queries
    assert any(
        '"medical nutrition therapy"' in query
        or '"nutrition"' in query
        or '"healthy eating"' in query
        for query in broad_lifestyle_queries
    )


def test_busca2b_semantics_include_therapeutic_carbohydrate_restriction() -> None:
    terms = [term.lower() for term in semantic_terms("busca2b", min_priority=5)]
    document_terms = [
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=5)
    ]

    assert "therapeutic carbohydrate restriction" in terms
    assert "low-carbohydrate dietary intervention" in terms
    assert "low carbohydrate diabetes remission" in terms
    assert "therapeutic carbohydrate restriction systematic review" in document_terms
    assert "carbohydrate restriction diabetes remission trial" in document_terms
