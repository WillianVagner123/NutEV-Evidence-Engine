from __future__ import annotations

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
            "obesity": ["obesity", "overweight"],
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
                "document_type_keys": ["reviews", "trials"],
                "priority_outcomes": ["anthropometry", "diet_quality_adherence"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["behavior change trial"],
            },
        },
    }


def test_nutrition_prescription_terms_enter_semantic_blocks() -> None:
    terms = semantic_terms("busca2b", min_priority=5)
    document_terms = semantic_terms(
        "busca2b",
        field="document_terms",
        min_priority=5,
    )

    assert "nutrition prescription" in terms
    assert "dietary prescription" in terms
    assert "personalized nutrition prescription" in terms
    assert "nutrition prescription guideline" in document_terms
    assert "dietary prescription protocol" in document_terms


def test_nutrition_prescription_terms_enter_provider_queries() -> None:
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert '"nutrition prescription"[Title/Abstract]' in joined
    assert '"dietary prescription"[Title/Abstract]' in joined
    assert '"nutrition prescription guideline"[Title/Abstract]' in joined
