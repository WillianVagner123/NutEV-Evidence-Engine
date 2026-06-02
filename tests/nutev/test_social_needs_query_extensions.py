from nutev.querypacks.provider_queries import render_queries_for_provider


def test_provider_queries_include_social_needs_food_access_terms_for_busca2b():
    tax = {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["implementation study"],
            }
        },
    }

    queries = render_queries_for_provider(tax, "busca2b", "pubmed")

    assert any(
        "food insecurity screening" in query
        or "social needs screening" in query
        or "community health worker nutrition" in query
        or "food pharmacy" in query
        for query in queries
    )
    assert any(
        "food insecurity screening program" in query
        or "social needs screening program" in query
        or "community health worker intervention" in query
        or "food pharmacy program" in query
        for query in queries
    )
