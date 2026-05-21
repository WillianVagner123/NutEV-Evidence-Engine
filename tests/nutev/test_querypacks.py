from nutev.querypacks.builders import build_queries, build_querypack


def test_build_querypack():
    tax = {"workstreams": {"busca1": {"base_terms": ["a"], "themes": ["b", "c"]}}}
    qp = build_querypack(tax, ["busca1"])
    assert len(qp["busca1"]) == 2


def test_build_queries_excludes_free_text_title_and_question():
    tax = {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "implementation_behavior": {"adherence": ["adherence"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["fiber"]},
        },
        "clinical": {"obesity": ["obesity"]},
        "outcomes": {"anthropometry": ["weight loss"]},
        "workstreams": {
            "busca1": {
                "title": "Free text title that should not run as query",
                "research_question": "Natural language question that should not run as query",
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["anthropometry"],
                "focus_blocks": ["diet_patterns"],
                "web_query_hints": ["food guideline"],
            }
        },
    }

    queries = build_queries(tax, "busca1")

    assert "Free text title that should not run as query" not in queries
    assert "Natural language question that should not run as query" not in queries
    assert any('"adult"' in query for query in queries)
    assert any('"obesity"' in query for query in queries)


def test_build_queries_adds_capture_biased_variants():
    tax = {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "implementation_behavior": {"adherence": ["adherence"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["fiber"]},
        },
        "clinical": {"obesity": ["obesity"]},
        "outcomes": {"anthropometry": ["weight loss"]},
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["anthropometry"],
                "focus_blocks": ["nutrition_domains"],
                "web_query_hints": ["clinical practice guideline"],
            }
        },
    }

    queries = build_queries(tax, "busca2a")

    assert any("filetype:pdf" in query for query in queries)
    assert any("open access" in query or "free full text" in query for query in queries)
    assert any("clinical practice guideline" in query for query in queries)


def test_build_querypack_resolves_a3_alias():
    tax = {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            "artigo3_framework": {
                "population_terms": ["adult"],
                "condition_terms": ["food literacy"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["implementation_behavior"],
                "web_query_hints": ["framework"],
            }
        },
    }

    qp = build_querypack(tax, ["a3"])

    assert qp["a3"]


def test_artigo3_queries_include_advanced_review_synthesis_terms():
    tax = {
        "global": {
            "document_types": {
                "reviews": [
                    "network meta-analysis",
                    "overview of reviews",
                    "living systematic review",
                ]
            },
            "implementation_behavior": {"behavioral": ["behavior change", "self-efficacy"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {
                "core": ["food literacy", "culinary medicine", "meal planning"]
            },
        },
        "clinical": {"obesity": ["obesity"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            "artigo3_framework": {
                "population_terms": ["adult"],
                "condition_terms": ["food literacy", "commensality"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["nutrition_domains", "implementation_behavior"],
                "web_query_hints": ["framework", "questionnaire validation"],
            }
        },
    }

    queries = build_queries(tax, "artigo3_framework")

    assert any("network meta-analysis" in query for query in queries)
    assert any("overview of reviews" in query for query in queries)
    assert any("living systematic review" in query for query in queries)
    assert any("food literacy" in query and "questionnaire" in query for query in queries)
