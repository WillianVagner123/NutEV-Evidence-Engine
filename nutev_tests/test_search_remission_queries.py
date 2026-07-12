from __future__ import annotations

from nutev.querypacks.builders import build_queries
from nutev.querypacks.provider_queries import render_queries_for_provider


def _busca2b_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {
            "obesity": ["obesity"],
            "diabetes": ["type 2 diabetes"],
        },
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


def test_busca2b_queries_include_metabolic_remission_and_maintenance_block() -> None:
    queries = build_queries(_busca2b_taxonomy(), "busca2b")

    assert any("type 2 diabetes remission" in query for query in queries)
    assert any("weight loss maintenance" in query for query in queries)
    assert any("dietary self-monitoring" in query for query in queries)
    assert any(
        "nutrition" in query and "cardiometabolic" in query
        for query in queries
        if "type 2 diabetes remission" in query
    )


def test_pubmed_queries_include_remission_and_weight_regain_signals() -> None:
    queries = render_queries_for_provider(_busca2b_taxonomy(), "busca2b", "pubmed")

    assert any('"type 2 diabetes remission"[Title/Abstract]' in query for query in queries)
    assert any('"weight regain prevention"[Title/Abstract]' in query for query in queries)
    assert any('"dietary self-regulation"[Title/Abstract]' in query for query in queries)
