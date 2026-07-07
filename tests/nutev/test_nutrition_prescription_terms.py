from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _minimal_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {
                "reviews": ["systematic review"],
                "trials": ["randomized controlled trial"],
            },
            "implementation_behavior": {"behavioral": ["dietary adherence"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["medical nutrition therapy"]},
        },
        "clinical": {
            "obesity": ["obesity"],
            "diabetes": ["type 2 diabetes"],
        },
        "outcomes": {
            "anthropometry": ["weight loss"],
            "metabolic": ["glycemic control"],
        },
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews", "trials"],
                "priority_outcomes": ["anthropometry", "metabolic"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["implementation study"],
            },
        },
    }


def test_nutrition_prescription_terms_extend_high_priority_busca2b_blocks() -> None:
    terms = semantic_terms("busca2b", min_priority=5)

    assert "nutrition prescription" in terms
    assert "dietary prescription for type 2 diabetes" in terms
    assert "lifestyle medicine prescription" in terms


def test_pubmed_queries_surface_nutrition_prescription_terms_for_busca2b() -> None:
    queries = render_queries_for_provider(_minimal_taxonomy(), "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "nutrition prescription" in rendered
    assert "dietary prescription for type 2 diabetes" in rendered
    assert "lifestyle medicine prescription" in rendered
