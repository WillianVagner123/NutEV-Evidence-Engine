from __future__ import annotations

import usercustomize  # noqa: F401

from nutev.querypacks.builders import build_queries
from nutev.querypacks.provider_queries import render_queries_for_provider


def _minimal_busca2b_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["medical nutrition therapy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["implementation_behavior", "nutrition_domains"],
                "web_query_hints": ["implementation study"],
            }
        },
    }


def test_busca2b_build_queries_include_anchored_group_delivery_models() -> None:
    queries = build_queries(_minimal_busca2b_taxonomy(), "busca2b")

    group_queries = [query for query in queries if "shared medical appointment" in query]

    assert group_queries
    assert all("obesity" in query or "type 2 diabetes" in query for query in group_queries)
    assert all("medical nutrition therapy" in query or "lifestyle intervention" in query for query in group_queries)


def test_pubmed_provider_queries_include_anchored_group_delivery_models() -> None:
    queries = render_queries_for_provider(_minimal_busca2b_taxonomy(), "busca2b", "pubmed")

    group_queries = [query for query in queries if "group medical visit" in query]

    assert group_queries
    assert all('"obesity"[Title/Abstract]' in query or '"type 2 diabetes"[Title/Abstract]' in query for query in group_queries)
    assert all('"nutrition"[Title/Abstract]' in query or '"medical nutrition therapy"[Title/Abstract]' in query for query in group_queries)
