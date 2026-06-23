from __future__ import annotations

from nutev.querypacks.builders import build_structured_components


MINIMAL_KEYWORD_TAXONOMY = {
    "global": {
        "nutrition_domains": {
            "core": [
                "nutrition",
                "food",
                "medical nutrition therapy",
                "dietary pattern",
            ]
        },
        "diet_patterns": {"core": ["healthy diet", "dietary pattern"]},
        "implementation_behavior": {
            "core": ["implementation", "dietary adherence"]
        },
        "document_types": {"trials": ["randomized trial"]},
    },
    "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
    "outcomes": {"metabolic": ["cardiometabolic risk"]},
    "workstreams": {
        "busca1": {
            "population_terms": ["adults"],
            "condition_terms": ["obesity"],
            "clinical_keys": ["obesity"],
            "priority_outcomes": ["metabolic"],
            "document_type_keys": ["trials"],
            "focus_blocks": ["nutrition_domains"],
            "web_query_hints": [],
        },
        "busca2b": {
            "population_terms": ["adults"],
            "condition_terms": ["obesity"],
            "clinical_keys": ["obesity", "diabetes"],
            "priority_outcomes": ["metabolic"],
            "document_type_keys": ["trials"],
            "focus_blocks": ["nutrition_domains", "implementation_behavior"],
            "web_query_hints": [],
        },
    },
}


def test_social_prescribing_terms_expand_busca1_food_access_layer() -> None:
    _, components = build_structured_components(MINIMAL_KEYWORD_TAXONOMY, "busca1")

    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}

    assert "social prescribing" in focus_terms
    assert "food pantry referral" in focus_terms
    assert "nutrition security referral" in focus_terms
    assert "community health worker-led nutrition" in focus_terms
    assert "food as medicine referral" in web_hints


def test_social_prescribing_terms_expand_busca2b_implementation_layer() -> None:
    _, components = build_structured_components(MINIMAL_KEYWORD_TAXONOMY, "busca2b")

    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}

    assert "social prescribing programme" in focus_terms
    assert "community resource referral" in focus_terms
    assert "food as medicine referral" in focus_terms
    assert "produce prescription referral" in web_hints
    assert "medically tailored food referral" in web_hints
