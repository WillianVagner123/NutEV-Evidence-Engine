from __future__ import annotations

from nutev.querypacks.builders import build_queries


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
