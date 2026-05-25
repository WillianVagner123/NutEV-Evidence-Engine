from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import _augment_with_semantic_blocks


def test_augment_with_semantic_blocks_prioritizes_semantic_terms_over_generic_focus_terms():
    taxonomy = {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "implementation_behavior": {"adherence": ["adherence"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {
                "core": [
                    "alpha nutrition term",
                    "beta nutrition term",
                    "gamma nutrition term",
                    "delta nutrition term",
                    "epsilon nutrition term",
                    "zeta nutrition term",
                ]
            },
        },
        "clinical": {"obesity": ["obesity"]},
        "outcomes": {"anthropometry": ["weight loss"]},
        "workstreams": {
            "busca1": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["anthropometry"],
                "focus_blocks": ["nutrition_domains"],
                "web_query_hints": ["food guideline"],
            }
        },
    }

    _, components = build_structured_components(taxonomy, "busca1")
    enriched = _augment_with_semantic_blocks("busca1", components)

    first_five_semantic_terms = enriched["semantic_terms"][:5]

    assert "food is medicine" in first_five_semantic_terms
    assert "food as medicine" in first_five_semantic_terms
    assert "alpha nutrition term" not in first_five_semantic_terms
