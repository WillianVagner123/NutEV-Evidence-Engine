from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components


def test_structured_components_expand_prediabetes_synonyms_for_busca2a() -> None:
    taxonomy = {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "implementation_behavior": {"adherence": ["adherence"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["fiber"]},
        },
        "clinical": {
            "obesity": ["obesity"],
            "prediabetes": [
                "prediabetes",
                "pre-diabetes",
                "prediabetic state",
                "impaired fasting glucose",
                "impaired glucose tolerance",
            ],
        },
        "outcomes": {"glycemia": ["hba1c"]},
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity", "prediabetes"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["glycemia"],
                "focus_blocks": ["diet_patterns"],
                "web_query_hints": ["clinical practice guideline"],
            }
        },
    }

    _, components = build_structured_components(taxonomy, "busca2a")

    assert "pre-diabetes" in components["condition_terms"]
    assert "prediabetic state" in components["condition_terms"]
    assert "impaired fasting glucose" in components["condition_terms"]
    assert "impaired glucose tolerance" in components["condition_terms"]
    assert "pre-diabetes" in components["focus_terms"]


def test_busca2a_scoring_boosts_prediabetes_language() -> None:
    base_record = {
        "source": "pubmed",
        "url": "https://example.org/guideline",
        "abstract": "Adult obesity nutrition care and cardiometabolic risk management.",
        "journal": "",
        "source_institution": "",
    }

    generic = score_record(
        {
            **base_record,
            "title": "Guideline for adult obesity nutrition care",
        },
        {},
        "busca2a",
    )
    prediabetes_focused = score_record(
        {
            **base_record,
            "title": "Guideline for adult obesity and pre-diabetes nutrition care",
        },
        {},
        "busca2a",
    )

    assert prediabetes_focused["relevance_score"] > generic["relevance_score"]
