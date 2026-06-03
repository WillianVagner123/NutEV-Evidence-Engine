from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _sample_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {
                "reviews": ["systematic review"],
                "trials": ["randomized controlled trial"],
            },
            "implementation_behavior": {
                "adherence": ["adherence", "implementation"],
            },
            "diet_patterns": {
                "core": ["healthy diet", "mediterranean diet"],
            },
            "nutrition_domains": {
                "core": ["medical nutrition therapy", "meal planning"],
            },
        },
        "clinical": {
            "obesity": ["obesity"],
            "diabetes": ["type 2 diabetes"],
        },
        "outcomes": {
            "anthropometry": ["weight loss"],
            "diet_quality_adherence": ["diet quality", "adherence"],
        },
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["trials", "reviews"],
                "priority_outcomes": ["anthropometry", "diet_quality_adherence"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["behavior change trial"],
            }
        },
    }


def test_nutrition_care_delivery_extensions_are_high_priority_for_busca2b() -> None:
    terms = semantic_terms("busca2b", min_priority=5)
    doc_terms = semantic_terms("busca2b", field="document_terms", min_priority=5)

    assert "nutrition care intervention" in terms
    assert "telehealth nutrition counseling" in terms
    assert "medical nutrition therapy trial" in doc_terms
    assert "pragmatic nutrition trial" in doc_terms


def test_nutrition_care_delivery_extensions_reach_provider_queries() -> None:
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert '"nutrition care intervention"[Title/Abstract]' in joined
    assert '"telehealth nutrition counseling"[Title/Abstract]' in joined
    assert '"pragmatic nutrition trial"[Title/Abstract]' in joined
