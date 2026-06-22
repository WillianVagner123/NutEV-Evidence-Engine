from __future__ import annotations

from nutev.querypacks.builders import build_structured_components


MINIMAL_TAXONOMY = {
    "global": {
        "document_types": {"guidelines": ["guideline"], "reviews": ["systematic review"]},
        "diet_patterns": ["mediterranean diet"],
        "nutrition_domains": ["medical nutrition therapy"],
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


def test_metabolic_remission_terms_are_added_to_cardiometabolic_workstreams() -> None:
    for workstream in ("busca2a", "busca2b"):
        _, components = build_structured_components(MINIMAL_TAXONOMY, workstream)

        assert "type 2 diabetes remission" in components["focus_terms"]
        assert "diabetes remission" in components["priority_outcomes"]
        assert "weight loss maintenance" in components["priority_outcomes"]
        assert "weight regain prevention" in components["priority_outcomes"]
        assert "diabetes remission guideline" in components["web_hints"]
        assert "diabetes remission consensus report" in components["web_hints"]
        assert "weight loss maintenance trial" in components["web_hints"]
        assert "remission consensus report" in components["doc_type_terms"]
        assert "weight loss maintenance systematic review" in components["doc_type_terms"]


def test_metabolic_remission_terms_do_not_expand_busca1_guideline_search() -> None:
    _, components = build_structured_components(MINIMAL_TAXONOMY, "busca1")

    assert "type 2 diabetes remission" not in components["focus_terms"]
    assert "diabetes remission" not in components["priority_outcomes"]
    assert "diabetes remission guideline" not in components["web_hints"]
    assert "remission consensus report" not in components["doc_type_terms"]
