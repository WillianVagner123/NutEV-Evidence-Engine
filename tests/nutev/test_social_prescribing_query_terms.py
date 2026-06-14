from __future__ import annotations

from nutev.querypacks.builders import build_structured_components


def _minimal_taxonomy(workstream: str) -> dict:
    return {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            workstream: {
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


def test_busca1_components_include_social_prescribing_food_access_terms() -> None:
    _, components = build_structured_components(_minimal_taxonomy("busca1"), "busca1")

    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}

    assert "social prescribing" in focus_terms
    assert "social prescribing program" in focus_terms
    assert "food as medicine referral" in focus_terms
    assert "produce prescription referral" in focus_terms
    assert "social prescribing" in web_hints
    assert "nutrition security referral" in web_hints


def test_busca2b_components_include_social_prescribing_food_access_terms() -> None:
    _, components = build_structured_components(_minimal_taxonomy("busca2b"), "busca2b")

    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}

    assert "social prescribing" in focus_terms
    assert "community resource referral" in focus_terms
    assert "food pantry referral program" in focus_terms
    assert "medically tailored food referral" in focus_terms
    assert "social prescribing programme" in web_hints
    assert "community health worker led nutrition" in web_hints
