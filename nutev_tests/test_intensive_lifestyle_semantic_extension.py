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


def test_intensive_lifestyle_program_terms_enter_semantic_blocks() -> None:
    busca2b_terms = semantic_terms("busca2b", min_priority=5)
    busca2b_doc_terms = semantic_terms(
        "busca2b",
        field="document_terms",
        min_priority=5,
    )

    assert "intensive lifestyle intervention" in busca2b_terms
    assert "diabetes prevention programme" in busca2b_terms
    assert "weight loss maintenance" in busca2b_terms
    assert "intensive lifestyle intervention trial" in busca2b_doc_terms
    assert "behavioral weight loss trial" in busca2b_doc_terms


def test_intensive_lifestyle_program_terms_enter_provider_queries() -> None:
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert '"intensive lifestyle intervention"[Title/Abstract]' in joined
    assert '"diabetes prevention programme"[Title/Abstract]' in joined
    assert '"behavioral weight loss trial"[Title/Abstract]' in joined


def test_metabolic_remission_terms_enter_semantic_blocks() -> None:
    busca2b_terms = semantic_terms("busca2b", min_priority=5)
    busca2b_doc_terms = semantic_terms(
        "busca2b",
        field="document_terms",
        min_priority=5,
    )

    assert "type 2 diabetes remission" in busca2b_terms
    assert "glycemic remission" in busca2b_terms
    assert "diabetes reversal" in busca2b_terms
    assert "weight regain prevention" in busca2b_terms
    assert "diabetes remission consensus report" in busca2b_doc_terms
    assert "weight regain prevention trial" in busca2b_doc_terms


def test_metabolic_remission_terms_enter_provider_queries() -> None:
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert '"type 2 diabetes remission"[Title/Abstract]' in joined
    assert '"glycemic remission"[Title/Abstract]' in joined
    assert '"diabetes remission consensus report"[Title/Abstract]' in joined