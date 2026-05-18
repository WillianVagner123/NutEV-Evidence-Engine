from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider


def _minimal_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "implementation_behavior": {"adherence": ["adherence"]},
            "diet_patterns": {"core": ["mediterranean diet"]},
            "nutrition_domains": {"core": ["fiber"]},
        },
        "clinical": {"obesity": ["obesity"]},
        "outcomes": {"glycemia": ["hba1c"]},
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["glycemia"],
                "focus_blocks": ["diet_patterns"],
                "web_query_hints": ["clinical practice guideline"],
            }
        },
    }


def test_render_queries_for_provider_adds_current_steatotic_liver_terms_to_busca2a():
    queries = render_queries_for_provider(
        _minimal_taxonomy(),
        "busca2a",
        "pubmed",
    )

    rendered = " ".join(queries).lower()

    assert '"steatohepatitis, non-alcoholic"[mesh terms]' in rendered
    assert '"non-alcoholic fatty liver disease"[mesh terms]' in rendered
    assert '"mash"[title/abstract]' in rendered


def test_score_record_rewards_current_steatotic_liver_terminology():
    scoring_rules = {
        "keyword_points": {
            "mash": 2,
            "steatotic liver disease": 3,
        },
        "source_points": {},
        "workstream_points": {},
        "editorial_authority_points": {},
    }

    base = score_record(
        {"title": "Lifestyle intervention in adults", "source": "pubmed"},
        scoring_rules,
        "busca2b",
    )
    enriched = score_record(
        {
            "title": "Lifestyle intervention in adults with MASH and steatotic liver disease",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert enriched["relevance_score"] >= base["relevance_score"] + 5
