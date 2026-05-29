from nutev.querypacks.provider_queries import render_queries_for_provider


def _minimal_busca2b_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"core": ["adherence"]},
            "diet_patterns": {"core": ["healthy dietary pattern"]},
            "nutrition_domains": {"core": ["medical nutrition therapy"]},
        },
        "clinical": {"metabolic": ["obesity", "type 2 diabetes"]},
        "outcomes": {"metabolic": ["glycemic control"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["metabolic"],
                "priority_outcomes": ["metabolic"],
                "document_type_keys": ["reviews"],
                "focus_blocks": ["nutrition_domains", "implementation_behavior"],
                "web_query_hints": ["implementation study"],
            }
        },
    }


def test_busca2b_pubmed_queries_include_food_access_practice_terms() -> None:
    queries = render_queries_for_provider(
        _minimal_busca2b_taxonomy(),
        "busca2b",
        "pubmed",
    )
    rendered = "\n".join(queries).lower()

    assert '"food pharmacy"[title/abstract]' in rendered
    assert '"fresh food pharmacy"[title/abstract]' in rendered
    assert '"social prescribing"[title/abstract]' in rendered
    assert '"nutrition prescription"[title/abstract]' in rendered
