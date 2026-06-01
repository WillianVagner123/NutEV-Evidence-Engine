from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _sample_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {
                "guidelines": ["clinical practice guideline"],
                "reviews": ["systematic review"],
            },
            "implementation_behavior": {
                "core": ["adherence", "implementation"],
            },
            "diet_patterns": {
                "core": ["mediterranean diet", "dietary pattern"],
            },
            "nutrition_domains": {
                "core": ["medical nutrition therapy", "nutrition counseling"],
            },
        },
        "clinical": {
            "obesity": ["obesity"],
            "metabolic": ["type 2 diabetes", "cardiometabolic risk"],
        },
        "outcomes": {
            "liver": ["liver fat", "hepatic steatosis"],
        },
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity", "metabolic"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["liver"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["nutrition intervention"],
            },
        },
    }


def test_liver_steatosis_terms_enter_busca2_semantic_blocks() -> None:
    busca2a_terms = set(semantic_terms("busca2a", min_priority=5))
    busca2b_terms = set(semantic_terms("busca2b", min_priority=5))

    expected_terms = {
        "hepatic steatosis",
        "liver fat",
        "intrahepatic fat",
        "liver fat content",
    }

    assert expected_terms.issubset(busca2a_terms)
    assert expected_terms.issubset(busca2b_terms)


def test_liver_steatosis_terms_enter_provider_queries() -> None:
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert '"hepatic steatosis"[Title/Abstract]' in joined
    assert '"liver fat"[Title/Abstract]' in joined
    assert '"hepatic steatosis systematic review"[Title/Abstract]' in joined
