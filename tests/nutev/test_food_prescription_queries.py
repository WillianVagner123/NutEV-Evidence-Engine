from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _minimal_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"guidelines": ["guideline"], "reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {
            "anthropometry": ["weight loss"],
            "behavioral": ["self efficacy"],
        },
        "workstreams": {
            "busca1": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["anthropometry"],
                "focus_blocks": ["nutrition_domains", "implementation_behavior"],
                "web_query_hints": ["food guideline"],
            },
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["implementation study"],
            },
        },
    }


def test_semantic_terms_prioritize_food_prescription_block_for_busca1_and_busca2b():
    busca1_terms = semantic_terms("busca1", min_priority=5)
    busca2b_terms = semantic_terms("busca2b", min_priority=5)

    assert busca1_terms[:3] == ["food is medicine", "food as medicine", "food is medicine intervention"]
    assert busca2b_terms[:3] == ["food is medicine", "food as medicine", "food is medicine intervention"]
    assert "produce rx" in busca1_terms
    assert "food prescription program" in busca2b_terms


def test_provider_queries_include_food_prescription_synonyms_for_busca1_and_busca2b():
    tax = _minimal_taxonomy()

    busca1_queries = render_queries_for_provider(tax, "busca1", "pubmed")
    busca2b_queries = render_queries_for_provider(tax, "busca2b", "pubmed")

    assert any("produce rx" in query for query in busca1_queries)
    assert any(
        "fruit and vegetable prescription" in query
        or "healthy food prescription" in query
        or "food prescription program" in query
        for query in busca2b_queries
    )
