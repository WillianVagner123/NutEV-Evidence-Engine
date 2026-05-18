from nutev.analysis.relevance import keep_candidate_for_download, score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


SCORING_RULES = {
    "keyword_points": {},
    "source_points": {},
    "workstream_points": {},
    "editorial_authority_points": {},
}


MINIMAL_TAXONOMY = {
    "global": {
        "document_types": {
            "guidelines": ["guideline", "consensus statement"],
            "reviews": ["systematic review"],
        },
        "diet_patterns": {
            "core": ["healthy diet"],
        },
        "nutrition_domains": {
            "core": ["nutrition"],
        },
        "implementation_behavior": {
            "core": ["implementation"],
        },
    },
    "clinical": {
        "obesity": ["obesity"],
        "diabetes": ["type 2 diabetes"],
        "hypertension": ["hypertension"],
        "dyslipidemia": ["dyslipidemia"],
        "cvd": ["cardiometabolic risk"],
        "metabolic_syndrome": ["metabolic syndrome"],
        "fatty_liver": ["masld", "steatotic liver disease"],
    },
    "outcomes": {
        "glycemia": ["hba1c"],
        "lipids": ["ldl"],
    },
    "workstreams": {
        "busca2a": {
            "population_terms": ["adult"],
            "condition_terms": ["obesity", "masld"],
            "clinical_keys": [
                "obesity",
                "diabetes",
                "hypertension",
                "dyslipidemia",
                "cvd",
                "metabolic_syndrome",
                "fatty_liver",
            ],
            "document_type_keys": ["guidelines", "reviews"],
            "priority_outcomes": ["glycemia", "lipids"],
            "focus_blocks": ["diet_patterns", "nutrition_domains", "implementation_behavior"],
            "web_query_hints": ["clinical practice guideline"],
        }
    },
}


def test_semantic_terms_include_modern_steatotic_liver_labels():
    terms = semantic_terms("busca2a", min_priority=4)

    assert "mash" in terms
    assert "steatotic liver disease" in terms
    assert "metabolic dysfunction-associated steatotic liver disease" in terms


def test_pubmed_queries_include_modern_steatotic_liver_terms():
    queries = render_queries_for_provider(MINIMAL_TAXONOMY, "busca2a", "pubmed")
    joined = "\n".join(queries).lower()

    assert '"mash"[title/abstract]' in joined or '"steatotic liver disease"[title/abstract]' in joined
    assert '"non-alcoholic fatty liver disease"[mesh terms]' in joined


def test_relevance_and_download_gate_promote_mash_consensus_records():
    record = {
        "source": "pubmed",
        "title": "Consensus statement on MASH nutrition care for adults with obesity",
        "abstract": "Adults with steatotic liver disease and cardiometabolic risk received lifestyle medicine support.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/123456/",
    }

    scored = score_record(record, SCORING_RULES, "busca2a")

    assert scored["relevance_score"] >= 7
    assert keep_candidate_for_download(scored, "busca2a")
