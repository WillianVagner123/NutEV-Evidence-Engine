from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider


def _minimal_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "implementation_behavior": {},
            "diet_patterns": {},
            "nutrition_domains": {},
        },
        "clinical": {
            "fatty_liver": ["masld"],
        },
        "outcomes": {
            "glycemia": ["hba1c"],
        },
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["fatty_liver"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["glycemia"],
                "focus_blocks": [],
                "web_query_hints": ["guideline"],
            }
        },
    }


def test_provider_queries_include_workstream_enhancement_terms() -> None:
    queries = render_queries_for_provider(_minimal_taxonomy(), "busca2a", "pubmed")

    assert any("mafld" in query.lower() for query in queries)
    assert any(
        "metabolic dysfunction-associated steatotic liver disease" in query.lower()
        for query in queries
    )


def test_relevance_scoring_boosts_masld_and_lifestyle_intervention_terms() -> None:
    scoring_rules = {
        "keyword_points": {},
        "source_points": {},
        "workstream_points": {},
    }

    baseline = score_record(
        {
            "title": "Clinical practice guideline for obesity",
            "source": "pubmed",
            "url": "https://example.org/article",
        },
        scoring_rules,
        "busca2a",
    )["relevance_score"]
    boosted = score_record(
        {
            "title": (
                "Clinical practice guideline for MAFLD with therapeutic "
                "lifestyle changes"
            ),
            "source": "pubmed",
            "url": "https://example.org/article",
        },
        scoring_rules,
        "busca2a",
    )["relevance_score"]

    assert boosted > baseline
