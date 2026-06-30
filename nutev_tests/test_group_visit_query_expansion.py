from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import prioritized_semantic_blocks, semantic_terms


GROUP_VISIT_TERMS = {
    "shared medical appointment",
    "group nutrition counseling",
    "obesity group visit",
    "weight management group visit",
}


def _minimal_taxonomy() -> dict:
    return {
        "global": {
            "implementation_behavior": {"core": ["implementation"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["nutrition care"]},
            "document_types": {"reviews": ["systematic review"]},
        },
        "clinical": {"glycemia": ["type 2 diabetes"]},
        "outcomes": {"metabolic": ["cardiometabolic risk"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adults with obesity"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["glycemia"],
                "priority_outcomes": ["metabolic"],
                "document_type_keys": ["reviews"],
                "focus_blocks": [],
            }
        },
    }


def test_group_visit_terms_are_high_priority_for_busca2b() -> None:
    priorities = {
        str(item["name"]): int(item["priority"])
        for item in prioritized_semantic_blocks("busca2b")
    }
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}

    assert priorities["group_visit_nutrition_care"] == 5
    assert GROUP_VISIT_TERMS <= terms


def test_provider_queries_include_group_visit_terms() -> None:
    rendered = "\n".join(
        render_queries_for_provider(_minimal_taxonomy(), "busca2b", "pubmed")
    ).lower()

    assert "shared medical appointment" in rendered
    assert "group nutrition counseling" in rendered
    assert "obesity group visit" in rendered
    assert "weight management group visit" in rendered
