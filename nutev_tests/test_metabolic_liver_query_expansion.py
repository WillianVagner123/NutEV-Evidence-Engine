from __future__ import annotations

from nutev.querypacks.builders import build_structured_components


def test_busca2a_condition_terms_include_full_metabolic_liver_variants() -> None:
    taxonomy = {
        "global": {},
        "clinical": {},
        "outcomes": {},
        "workstreams": {
            "busca2a": {
                "population_terms": [],
                "condition_terms": ["obesity"],
                "clinical_keys": [],
                "document_type_keys": [],
                "priority_outcomes": [],
                "focus_blocks": [],
                "web_query_hints": [],
            }
        },
    }

    _, components = build_structured_components(taxonomy, "busca2a")
    terms = {term.lower() for term in components["condition_terms"]}

    expected = {
        "masld",
        "mafld",
        "nafld",
        "mash",
        "nash",
        "fatty liver",
        "nonalcoholic fatty liver disease",
        "non-alcoholic fatty liver disease",
        "nonalcoholic steatohepatitis",
        "non-alcoholic steatohepatitis",
        "metabolic dysfunction-associated fatty liver disease",
        "metabolic dysfunction associated fatty liver disease",
        "metabolic dysfunction-associated steatohepatitis",
        "metabolic dysfunction associated steatohepatitis",
    }

    assert expected.issubset(terms)
