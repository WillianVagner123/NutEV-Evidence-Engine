from nutev.querypacks.provider_queries import render_queries_for_provider


def _minimal_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {"guidelines": ["guideline"], "reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {
            "obesity": ["obesity"],
            "diabetes": ["type 2 diabetes"],
            "metabolic_syndrome": ["metabolic syndrome"],
        },
        "outcomes": {
            "glycemia": ["hba1c"],
            "behavioral": ["self efficacy"],
        },
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes", "metabolic_syndrome"],
                "document_type_keys": ["guidelines", "reviews"],
                "priority_outcomes": ["glycemia"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["clinical practice guideline"],
            },
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes", "metabolic_syndrome"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["glycemia", "behavioral"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["implementation study"],
            },
        },
    }


def test_provider_queries_include_prediabetes_signals_for_cardiometabolic_workstreams():
    taxonomy = _minimal_taxonomy()

    for workstream in ("busca2a", "busca2b"):
        queries = render_queries_for_provider(taxonomy, workstream, "pubmed")

        assert any(
            term in query
            for query in queries
            for term in (
                "prediabetes",
                "pre-diabetes",
                "impaired fasting glucose",
                "impaired glucose tolerance",
                "dysglycemia",
                "dysglycaemia",
            )
        )
        assert any(
            "obesity" in query or "type 2 diabetes" in query or "metabolic syndrome" in query
            for query in queries
        )
