from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider


def test_provider_queries_include_diet_quality_index_variants_for_busca2b() -> None:
    tax = {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["dietary adherence"]},
            "diet_patterns": {"core": ["diet quality"]},
            "nutrition_domains": {"core": ["medical nutrition therapy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"cardiometabolic": ["cardiometabolic risk"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["cardiometabolic"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["implementation study"],
            }
        },
    }

    queries = render_queries_for_provider(tax, "busca2b", "pubmed")

    assert any(
        "alternate healthy eating index 2010" in query
        or "healthy eating index 2015" in query
        for query in queries
    )
    assert any(
        "dash diet adherence score" in query
        or "mediterranean diet adherence score" in query
        or "healthful plant-based diet index" in query
        for query in queries
    )
