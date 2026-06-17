from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _sample_busca2b_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"adherence": ["adherence"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["medical nutrition therapy"]},
        },
        "clinical": {"obesity": ["obesity"]},
        "outcomes": {"cardiometabolic": ["cardiometabolic risk"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["cardiometabolic"],
                "focus_blocks": ["diet_patterns", "nutrition_domains"],
                "web_query_hints": ["dietary adherence"],
            },
        },
    }


def test_semantic_blocks_include_healthy_dietary_pattern_variants() -> None:
    busca2a_terms = semantic_terms("busca2a", min_priority=4)
    busca2b_terms = semantic_terms("busca2b", min_priority=5)

    for terms in (busca2a_terms, busca2b_terms):
        assert "healthy eating patterns" in terms
        assert "healthy dietary pattern" in terms
        assert "healthy dietary patterns" in terms
        assert "vegetarian diet" in terms
        assert "vegetarian dietary pattern" in terms
        assert "vegan diet" in terms
        assert "vegan dietary pattern" in terms
        assert "healthy plant-based diet" in terms


def test_semantic_blocks_include_sustainable_healthy_diet_variants() -> None:
    busca1_terms = semantic_terms("busca1", min_priority=5)
    busca2b_terms = semantic_terms("busca2b", min_priority=5)
    busca2b_doc_terms = semantic_terms(
        "busca2b",
        field="document_terms",
        min_priority=5,
    )

    for terms in (busca1_terms, busca2b_terms):
        assert "sustainable healthy diet" in terms
        assert "sustainable healthy diets" in terms
        assert "healthy sustainable diet" in terms
        assert "healthy and sustainable diets" in terms
        assert "sustainable dietary pattern" in terms
        assert "sustainable dietary patterns" in terms

    assert "sustainable healthy diet guideline" in busca2b_doc_terms
    assert "sustainable dietary patterns systematic review" in busca2b_doc_terms
    assert "planetary health diet systematic review" in busca2b_doc_terms


def test_semantic_blocks_include_ultra_processed_food_variants() -> None:
    busca2a_terms = semantic_terms("busca2a", min_priority=4)
    busca2b_terms = semantic_terms("busca2b", min_priority=5)
    busca2b_doc_terms = semantic_terms(
        "busca2b",
        field="document_terms",
        min_priority=5,
    )

    for terms in (busca2a_terms, busca2b_terms):
        assert "ultra-processed food" in terms
        assert "ultra processed foods" in terms
        assert "nova classification" in terms
        assert "upf consumption" in terms

    assert "ultra-processed food systematic review" in busca2b_doc_terms
    assert "nova classification meta-analysis" in busca2b_doc_terms


def test_ultra_processed_food_terms_enter_provider_queries() -> None:
    queries = render_queries_for_provider(
        _sample_busca2b_taxonomy(),
        "busca2b",
        "pubmed",
    )
    joined = "\n".join(queries)

    assert '"ultra-processed food"[Title/Abstract]' in joined
    assert '"nova classification"[Title/Abstract]' in joined
    assert '"ultra-processed food systematic review"[Title/Abstract]' in joined


def test_sustainable_healthy_diet_terms_enter_provider_queries() -> None:
    queries = render_queries_for_provider(
        _sample_busca2b_taxonomy(),
        "busca2b",
        "pubmed",
    )
    joined = "\n".join(queries)

    assert '"sustainable healthy diet"[Title/Abstract]' in joined
    assert '"sustainable dietary pattern"[Title/Abstract]' in joined
    assert '"sustainable healthy diet guideline"[Title/Abstract]' in joined
