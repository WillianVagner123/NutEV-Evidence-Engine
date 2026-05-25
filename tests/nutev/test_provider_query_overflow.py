from nutev.querypacks.provider_queries import render_queries_for_provider


def test_provider_queries_preserve_tail_web_hints_for_busca2b():
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
        "masld trial" in query
        or "nafld trial" in query
        or "steatotic liver disease trial" in query
        or "lipid lowering trial" in query
        for query in queries
    )
