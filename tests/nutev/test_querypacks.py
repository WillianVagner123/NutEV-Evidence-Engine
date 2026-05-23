import json
from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_queries, build_querypack
from nutev.querypacks.provider_queries import render_queries_for_provider


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


def test_provider_queries_include_nutrition_delivery_terms_for_busca2b():
    tax = {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["implementation study"],
            }
        },
    }

    queries = render_queries_for_provider(tax, "busca2b", "pubmed")

    assert any("food is medicine" in query for query in queries)
    assert any("food as medicine" in query for query in queries)
    assert any(
        "registered dietitian nutritionist" in query
        or "dietitian-led intervention" in query
        for query in queries
    )
    assert any(
        "re-aim" in query
        or "cfir" in query
        or "consolidated framework for implementation research" in query
        or "hybrid effectiveness-implementation" in query
        for query in queries
    )


def test_provider_queries_include_hybrid_type_and_process_evaluation_terms_for_busca2b():
    tax = {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["implementation study"],
            }
        },
    }

    queries = render_queries_for_provider(tax, "busca2b", "pubmed")

    assert any(
        "hybrid type 2" in query
        or "hybrid type 3" in query
        or "process evaluation" in query
        or "implementation trial" in query
        for query in queries
    )


def test_provider_queries_include_diabetes_standards_for_busca2a():
    tax = {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"glycemia": ["hba1c"]},
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["glycemia"],
                "focus_blocks": ["diet_patterns"],
                "web_query_hints": ["clinical practice guideline"],
            }
        },
    }

    queries = render_queries_for_provider(tax, "busca2a", "pubmed")

    assert any("standards of medical care in diabetes" in query for query in queries)
    assert any("consensus report" in query for query in queries)


def test_provider_queries_include_intensive_lifestyle_intervention_for_busca2b():
    tax = {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["implementation study"],
            }
        },
    }

    queries = render_queries_for_provider(tax, "busca2b", "pubmed")

    assert any("intensive lifestyle intervention" in query for query in queries)
    assert any(
        "lifestyle program" in query or "lifestyle programme" in query
        for query in queries
    )


def test_food_as_medicine_variant_scores_like_food_is_medicine():
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )
    base_record = {
        "source": "pubmed",
        "url": "https://example.org/article",
        "abstract": "Adult obesity intervention with medically tailored meals and implementation outcomes.",
        "journal": "",
        "source_institution": "",
    }

    food_is_medicine = score_record(
        {
            **base_record,
            "title": "Food is medicine intervention for adult obesity",
        },
        scoring_rules,
        "busca2b",
    )
    food_as_medicine = score_record(
        {
            **base_record,
            "title": "Food as medicine intervention for adult obesity",
        },
        scoring_rules,
        "busca2b",
    )

    assert food_as_medicine["relevance_score"] >= food_is_medicine["relevance_score"]


def test_busca2b_scoring_boosts_hybrid_implementation_designs():
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )
    base_record = {
        "source": "pubmed",
        "url": "https://example.org/article",
        "abstract": "Adult obesity care in primary care with food as medicine delivery and dietary support.",
        "journal": "",
        "source_institution": "",
    }

    standard_program = score_record(
        {
            **base_record,
            "title": "Food as medicine program for adult obesity in primary care",
        },
        scoring_rules,
        "busca2b",
    )
    hybrid_implementation = score_record(
        {
            **base_record,
            "title": "Hybrid type 2 implementation trial of a food as medicine program for adult obesity in primary care",
        },
        scoring_rules,
        "busca2b",
    )

    assert hybrid_implementation["relevance_score"] > standard_program["relevance_score"]


def test_scoring_boosts_diabetes_standards_and_intensive_lifestyle_intervention():
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )

    guideline_base = {
        "source": "pubmed",
        "url": "https://example.org/diabetes-guideline",
        "abstract": "Adult obesity and type 2 diabetes nutrition care.",
        "journal": "",
        "source_institution": "American Diabetes Association",
    }
    generic_guideline = score_record(
        {**guideline_base, "title": "Guideline for nutrition care in type 2 diabetes"},
        scoring_rules,
        "busca2a",
    )
    diabetes_standards = score_record(
        {
            **guideline_base,
            "title": "Standards of Medical Care in Diabetes for obesity and nutrition therapy",
        },
        scoring_rules,
        "busca2a",
    )

    intervention_base = {
        "source": "pubmed",
        "url": "https://example.org/lifestyle-intervention",
        "abstract": "Adult obesity and type 2 diabetes behavior change support in primary care.",
        "journal": "",
        "source_institution": "",
    }
    generic_intervention = score_record(
        {**intervention_base, "title": "Lifestyle intervention for adult obesity and diabetes"},
        scoring_rules,
        "busca2b",
    )
    intensive_intervention = score_record(
        {
            **intervention_base,
            "title": "Intensive lifestyle intervention program for adult obesity and type 2 diabetes",
        },
        scoring_rules,
        "busca2b",
    )

    assert diabetes_standards["relevance_score"] > generic_guideline["relevance_score"]
    assert intensive_intervention["relevance_score"] > generic_intervention["relevance_score"]
