from __future__ import annotations

from nutev.querypacks.builders import build_structured_components


MINIMAL_TAXONOMY = {
    "global": {
        "document_types": {"guidelines": ["guideline"]},
        "diet_patterns": ["mediterranean diet"],
        "nutrition_domains": ["nutrition counseling"],
        "implementation_behavior": ["adherence"],
    },
    "clinical": {},
    "outcomes": {},
    "workstreams": {
        "busca1": {
            "condition_terms": ["obesity"],
            "document_type_keys": ["guidelines"],
        },
        "busca2a": {
            "condition_terms": ["obesity"],
            "document_type_keys": ["guidelines"],
        },
        "busca2b": {
            "condition_terms": ["obesity"],
            "document_type_keys": ["reviews"],
        },
    },
}


def test_advanced_dyslipidemia_terms_are_added_to_cardiometabolic_workstreams() -> None:
    for workstream in ("busca2a", "busca2b"):
        _, components = build_structured_components(MINIMAL_TAXONOMY, workstream)

        assert "remnant cholesterol" in components["condition_terms"]
        assert "apolipoprotein b" in components["condition_terms"]
        assert "triglyceride-rich lipoprotein" in components["condition_terms"]
        assert "remnant cholesterol management" in components["focus_terms"]


def test_advanced_dyslipidemia_terms_do_not_expand_busca1_guideline_search() -> None:
    _, components = build_structured_components(MINIMAL_TAXONOMY, "busca1")

    assert "remnant cholesterol" not in components["condition_terms"]
    assert "apolipoprotein b" not in components["condition_terms"]
    assert "remnant cholesterol management" not in components["focus_terms"]
