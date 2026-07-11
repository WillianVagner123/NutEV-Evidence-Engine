from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _sample_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"adherence": ["adherence"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"]},
        "outcomes": {"diet_quality": ["diet quality"]},
        "workstreams": {
            "artigo3_framework": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["diet_quality"],
                "focus_blocks": ["nutrition_domains", "implementation_behavior"],
                "web_query_hints": ["questionnaire validation"],
            }
        },
    }


def test_food_literacy_measurement_terms_extend_semantic_block() -> None:
    terms = semantic_terms("artigo3_framework", min_priority=5)
    document_terms = semantic_terms(
        "artigo3_framework",
        field="document_terms",
        min_priority=5,
    )

    assert "functional food literacy" in terms
    assert "nutrition literacy assessment" in terms
    assert "food and nutrition literacy questionnaire" in document_terms


def test_food_literacy_measurement_terms_render_in_provider_queries() -> None:
    queries = render_queries_for_provider(
        _sample_taxonomy(),
        "artigo3_framework",
        "pubmed",
    )
    joined = "\n".join(queries)

    assert '"functional food literacy"[Title/Abstract]' in joined
    assert '"food and nutrition literacy questionnaire"[Title/Abstract]' in joined
