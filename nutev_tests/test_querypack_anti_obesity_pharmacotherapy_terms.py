from __future__ import annotations

from nutev.querypacks.builders import build_structured_components


MINIMAL_TAXONOMY = {
    "global": {
        "document_types": {"reviews": ["systematic review"]},
        "diet_patterns": ["mediterranean diet"],
        "nutrition_domains": ["medical nutrition therapy"],
        "implementation_behavior": ["adherence"],
    },
    "clinical": {},
    "outcomes": {},
    "workstreams": {
        "busca1": {
            "condition_terms": ["obesity"],
            "document_type_keys": ["reviews"],
        },
        "busca2a": {
            "condition_terms": ["obesity"],
            "document_type_keys": ["reviews"],
        },
        "busca2b": {
            "condition_terms": ["obesity"],
            "document_type_keys": ["reviews"],
        },
    },
}


def test_glp1_nutrition_terms_expand_cardiometabolic_workstreams() -> None:
    expected_focus_terms = {
        "anti-obesity medication nutrition",
        "glp-1 receptor agonist nutrition care",
        "incretin therapy nutrition care",
        "lean mass preservation",
        "protein adequacy",
    }
    expected_doc_terms = {
        "glp-1 nutrition guidance",
        "anti-obesity pharmacotherapy nutrition guideline",
        "lean mass preservation systematic review",
    }

    for workstream in ("busca2a", "busca2b"):
        _, components = build_structured_components(MINIMAL_TAXONOMY, workstream)
        focus_terms = {term.lower() for term in components["focus_terms"]}
        doc_terms = {term.lower() for term in components["doc_type_terms"]}

        assert {term.lower() for term in expected_focus_terms}.issubset(focus_terms)
        assert {term.lower() for term in expected_doc_terms}.issubset(doc_terms)


def test_glp1_nutrition_terms_are_lower_priority_for_busca1() -> None:
    _, components = build_structured_components(MINIMAL_TAXONOMY, "busca1")
    terms = {term.lower() for term in components["focus_terms"]}

    assert "anti-obesity medication nutrition" in terms
    assert "lean mass preservation" in terms
