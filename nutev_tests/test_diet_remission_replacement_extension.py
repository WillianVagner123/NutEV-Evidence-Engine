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


def test_diet_remission_replacement_terms_enter_semantic_blocks() -> None:
    terms = semantic_terms("busca2b", min_priority=5)
    document_terms = semantic_terms(
        "busca2b",
        field="document_terms",
        min_priority=5,
    )

    assert "low energy total diet replacement" in terms
    assert "very low calorie diet program" in terms
    assert "diabetes remission program" in terms
    assert "DiRECT trial" in terms
    assert "Counterweight Plus" in terms
    assert "total diet replacement trial" in document_terms
    assert "diabetes remission program evaluation" in document_terms


def test_diet_remission_replacement_terms_enter_provider_queries() -> None:
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert '"low energy total diet replacement"[Title/Abstract]' in joined
    assert '"very low calorie diet program"[Title/Abstract]' in joined
    assert '"diabetes remission program"[Title/Abstract]' in joined
    assert '"DiRECT trial"[Title/Abstract]' in joined
    assert '"total diet replacement trial"[Title/Abstract]' in joined
