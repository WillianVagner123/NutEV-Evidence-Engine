from nutev.querypacks.provider_queries import render_queries_for_provider


def test_busca2b_pubmed_queries_include_dietitian_led_nutrition_focus_terms():
    taxonomy = {
        "global": {
            "implementation_behavior": {"adherence": ["adherence", "implementation science"]},
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

    assert "medical nutrition therapy" in rendered
    assert "registered dietitian nutritionist" in rendered
    assert "dietitian-led intervention" in rendered
    assert "implementation determinants" in rendered
    assert "implementation evaluation" in rendered
    assert "process evaluation" in rendered
    assert "real-world evidence" in rendered
    assert "hybrid type 1" in rendered
    assert "hybrid type 2" in rendered
    assert "motivational interviewing" in rendered
    assert "shared decision making" in rendered
    assert "self-management support" in rendered
    assert "meal replacement" in rendered
    assert "total diet replacement" in rendered
    assert "very low energy diet" in rendered


def test_busca2a_pubmed_queries_include_lifestyle_nutrition_pattern_terms():
    taxonomy = {
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
            }
        },
    }

    queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "therapeutic lifestyle changes" in rendered
    assert "mediterranean dietary pattern" in rendered
    assert "dietary approaches to stop hypertension" in rendered
    assert "practice guidance" in rendered
    assert "clinical decision pathway" in rendered
