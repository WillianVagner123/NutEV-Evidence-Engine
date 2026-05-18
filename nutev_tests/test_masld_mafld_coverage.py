from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import render_queries_for_provider


def _sample_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {
                "guidelines": ["guideline", "clinical practice guideline"],
                "reviews": ["systematic review"],
            },
            "implementation_behavior": {
                "adherence": ["adherence", "implementation"],
            },
            "diet_patterns": {
                "core": ["healthy diet", "mediterranean diet"],
            },
            "nutrition_domains": {
                "core": ["food literacy", "meal planning"],
            },
        },
        "clinical": {
            "obesity": ["obesity", "overweight"],
            "diabetes": ["type 2 diabetes"],
            "fatty_liver": ["fatty liver", "masld", "nafld"],
        },
        "outcomes": {
            "anthropometry": ["weight loss"],
            "glycemia": ["hba1c"],
            "lipids": ["ldl"],
        },
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity", "diabetes", "fatty_liver"],
                "document_type_keys": ["guidelines", "reviews"],
                "priority_outcomes": ["anthropometry", "glycemia", "lipids"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["clinical practice guideline"],
            }
        },
    }


def test_busca2a_structured_components_include_mafld_aliases():
    _, components = build_structured_components(_sample_taxonomy(), "busca2a")

    assert "mafld" in components["focus_terms"]
    assert "metabolic dysfunction-associated steatotic liver disease" in components["focus_terms"]
    assert "nonalcoholic fatty liver disease" in components["focus_terms"]
    assert "masld guideline" in components["web_hints"]


def test_pubmed_provider_queries_include_fatty_liver_aliases_and_mesh():
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2a", "pubmed")
    joined = "\n".join(queries).lower()

    assert "mafld" in joined or "metabolic dysfunction-associated steatotic liver disease" in joined
    assert "non-alcoholic fatty liver disease" in joined
    assert "[mesh terms]" in joined


def test_relevance_scoring_rewards_mafld_guideline_language():
    scoring_rules = {"keyword_points": {}, "source_points": {}, "workstream_points": {}}
    baseline = score_record(
        {"title": "clinical practice guideline for obesity management", "source": "pubmed"},
        scoring_rules,
        "busca2a",
    )
    enriched = score_record(
        {
            "title": "MAFLD clinical practice guideline for cardiometabolic risk management",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert enriched["relevance_score"] > baseline["relevance_score"]
