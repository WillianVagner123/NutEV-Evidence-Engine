from __future__ import annotations

from nutev.querypacks.builders import build_structured_components


def test_guideline_workstreams_include_expanded_guideline_variants() -> None:
    taxonomy = {
        "global": {
            "document_types": {
                "guidelines": ["guideline", "consensus"],
                "reviews": ["systematic review"],
                "trials": ["randomized controlled trial"],
            }
        },
        "clinical": {},
        "outcomes": {},
        "workstreams": {
            "busca2a": {
                "document_type_keys": ["guidelines", "reviews"],
                "population_terms": [],
                "condition_terms": [],
                "clinical_keys": [],
                "priority_outcomes": [],
                "focus_blocks": [],
                "web_query_hints": [],
            },
            "artigo3_framework": {
                "document_type_keys": ["reviews", "trials"],
                "population_terms": [],
                "condition_terms": [],
                "clinical_keys": [],
                "priority_outcomes": [],
                "focus_blocks": [],
                "web_query_hints": [],
            },
        },
    }

    _, busca2a = build_structured_components(taxonomy, "busca2a")
    _, artigo3 = build_structured_components(taxonomy, "artigo3_framework")

    expected = {
        "nutrition practice guideline",
        "dietetic practice guideline",
        "practice advisory",
        "policy statement",
        "consensus update",
        "clinical decision pathway",
        "clinical practice recommendations",
        "scientific advisory",
    }

    assert expected.issubset(set(busca2a["doc_type_terms"]))
    assert expected.isdisjoint(set(artigo3["doc_type_terms"]))
