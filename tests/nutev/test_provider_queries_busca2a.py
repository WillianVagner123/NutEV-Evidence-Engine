from nutev.querypacks.provider_queries import build_provider_querypack


def test_busca2a_provider_queries_include_guidance_expansion_terms():
    taxonomy = {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "implementation_behavior": {"adherence": ["adherence"]},
            "diet_patterns": {"core": ["mediterranean diet"]},
            "nutrition_domains": {"core": ["medical nutrition therapy"]},
        },
        "clinical": {
            "obesity": ["obesity"],
            "diabetes": ["type 2 diabetes"],
        },
        "outcomes": {"glycemia": ["hba1c"]},
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["glycemia"],
                "focus_blocks": ["nutrition_domains"],
                "web_query_hints": ["clinical practice guideline"],
            }
        },
    }

    provider_querypack = build_provider_querypack(
        taxonomy,
        ["busca2a"],
        {"busca2a": ["pubmed"]},
    )

    queries = provider_querypack["busca2a"]["pubmed"]

    assert any('"Practice Guideline"[Publication Type]' in query for query in queries)
    assert any('"guideline update"[Title/Abstract]' in query for query in queries)
    assert any('"clinical practice update"[Title/Abstract]' in query for query in queries)
