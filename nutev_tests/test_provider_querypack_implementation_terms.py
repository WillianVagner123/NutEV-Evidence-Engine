from nutev.querypacks.provider_queries import render_queries_for_provider


def test_busca2b_pubmed_queries_include_new_implementation_science_terms():
    taxonomy = {
        "global": {
            "implementation_behavior": {
                "adherence": ["adherence", "implementation science"]
            },
            "diet_patterns": {"core": ["mediterranean diet", "dash diet"]},
            "nutrition_domains": {"core": ["nutrition care"]},
            "document_types": {"reviews": ["systematic review"]},
        },
        "clinical": {"glycemia": ["type 2 diabetes"]},
        "outcomes": {"metabolic": ["glycemic control"]},
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

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "implementation science" in rendered
    assert "medical nutrition therapy" in rendered
    assert "registered dietitian nutritionist" in rendered
    assert "dietitian-led intervention" in rendered
