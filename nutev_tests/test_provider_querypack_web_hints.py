from nutev.querypacks.provider_queries import render_queries_for_provider


def _minimal_busca2a_taxonomy() -> dict:
    return {
        "global": {
            "implementation_behavior": {"core": ["adherence"]},
            "diet_patterns": {"core": ["mediterranean diet"]},
            "nutrition_domains": {"core": ["nutrition care"]},
            "document_types": {"guidance": ["guideline"]},
        },
        "clinical": {"glycemia": ["type 2 diabetes"]},
        "outcomes": {"metabolic": ["glycemic control"]},
        "workstreams": {
            "busca2a": {
                "population_terms": ["adults with obesity"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["glycemia"],
                "priority_outcomes": ["metabolic"],
                "document_type_keys": ["guidance"],
                "focus_blocks": [],
                "web_query_hints": ["practice guidance", "guidance statement"],
            }
        },
    }


def test_busca2a_europepmc_queries_include_web_hints_even_without_overflow() -> None:
    queries = render_queries_for_provider(
        _minimal_busca2a_taxonomy(),
        "busca2a",
        "europepmc",
    )
    rendered = "\n".join(queries).lower()

    assert 'title_abs:"practice guidance"' in rendered
    assert 'title_abs:"guidance statement"' in rendered


def test_busca2a_openalex_queries_include_web_hints_even_without_overflow() -> None:
    queries = render_queries_for_provider(
        _minimal_busca2a_taxonomy(),
        "busca2a",
        "openalex",
    )
    rendered = "\n".join(queries).lower()

    assert '"practice guidance"' in rendered
    assert '"guidance statement"' in rendered
