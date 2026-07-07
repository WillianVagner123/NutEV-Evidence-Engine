from pathlib import Path

from nutev.querypacks.provider_queries import (
    build_provider_querypack,
    render_queries_for_provider,
    write_provider_querypack_audit,
)
from nutev.querypacks.semantic_blocks import (
    prioritized_semantic_blocks,
    semantic_block_names,
    semantic_terms,
)


def _sample_taxonomy() -> dict:
    return {
        "global": {
            "document_types": {
                "guidelines": [
                    "guideline",
                    "clinical practice guideline",
                    "practice guidance",
                    "guidance statement",
                    "joint statement",
                    "living guideline",
                    "position paper",
                    "scientific statement",
                ],
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
        },
        "outcomes": {
            "anthropometry": ["weight loss"],
            "diet_quality_adherence": ["diet quality", "adherence"],
        },
        "workstreams": {
            "busca1": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity"],
                "document_type_keys": ["guidelines", "reviews"],
                "priority_outcomes": ["anthropometry", "diet_quality_adherence"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["food guideline"],
            },
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["anthropometry", "diet_quality_adherence"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["behavior change trial"],
            },
        },
    }


def test_pubmed_queries_use_fielded_terms():
    queries = render_queries_for_provider(_sample_taxonomy(), "busca1", "pubmed")

    assert queries
    assert any("[Title/Abstract]" in query for query in queries)
    assert any("[Publication Type]" in query or "[MeSH Terms]" in query for query in queries)


def test_europepmc_queries_use_title_abs():
    queries = render_queries_for_provider(_sample_taxonomy(), "busca1", "europepmc")

    assert queries
    assert all("TITLE_ABS:" in query for query in queries)


def test_provider_queries_include_semantic_research_blocks():
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert "implementation science" in joined
    assert "dietary adherence" in joined


def test_food_access_program_terms_are_promoted_into_provider_queries():
    queries = render_queries_for_provider(_sample_taxonomy(), "busca1", "pubmed")
    joined = "\n".join(queries)

    assert "healthy food incentive" in joined
    assert "produce voucher" in joined
    assert "medically tailored nutrition" in joined
    assert "food pharmacy programme" in joined
    assert "food farmacy programme" in joined


def test_semantic_blocks_are_prioritized_by_workstream():
    busca1_blocks = semantic_block_names("busca1")
    busca2b_terms = semantic_terms("busca2b", min_priority=5)
    priorities = prioritized_semantic_blocks("a3")

    assert busca1_blocks[:2] == ["food_literacy_agency", "commensality_context"]
    assert "implementation science" in busca2b_terms
    assert "adherence" in busca2b_terms
    assert priorities[0] == {"name": "food_literacy_agency", "priority": 5}


def test_busca1_semantic_blocks_include_food_environment_policy_terms() -> None:
    busca1_terms = semantic_terms("busca1", min_priority=5)
    busca1_doc_terms = semantic_terms(
        "busca1",
        field="document_terms",
        min_priority=5,
    )

    assert "retail food environment" in busca1_terms
    assert "healthy food procurement" in busca1_terms
    assert "menu labeling" in busca1_terms
    assert "policy brief" in busca1_doc_terms
    assert "policy evaluation" in busca1_doc_terms


def test_provider_querypack_builds_per_provider():
    querypack = build_provider_querypack(
        _sample_taxonomy(),
        ["busca1"],
        {"busca1": ["pubmed", "europepmc", "official_web"]},
    )

    assert "pubmed" in querypack["busca1"]
    assert "europepmc" in querypack["busca1"]
    assert "official_web" not in querypack["busca1"]


def test_provider_querypack_audit_files_are_written(tmp_path: Path):
    provider_querypack = {
        "busca1": {
            "pubmed": ['"obesity"[Title/Abstract]'],
            "europepmc": ['TITLE_ABS:"obesity"'],
        }
    }

    write_provider_querypack_audit(provider_querypack, tmp_path)

    json_path = tmp_path / "provider_querypack_executed.json"
    csv_path = tmp_path / "provider_querypack_executed.csv"
    assert json_path.exists()
    assert csv_path.exists()
    assert "semantic_blocks" in csv_path.read_text(encoding="utf-8")
    assert "food_literacy_agency:5" in csv_path.read_text(encoding="utf-8")


def test_doc_type_overflow_keeps_late_guideline_labels_visible():
    queries = render_queries_for_provider(_sample_taxonomy(), "busca1", "pubmed")
    joined = "\n".join(queries)

    assert '"living guideline"[Title/Abstract]' in joined
    assert '"position paper"[Publication Type]' in joined or '"position paper"[Title/Abstract]' in joined


def test_pubmed_mesh_expands_lipid_liver_and_prediabetes_terms() -> None:
    taxonomy = {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "diet_patterns": {"core": ["mediterranean diet"]},
            "nutrition_domains": {"core": ["medical nutrition therapy"]},
            "implementation_behavior": {"adherence": ["adherence"]},
        },
        "clinical": {
            "diabetes": ["prediabetes", "insulin resistance"],
            "lipids": ["dyslipidaemia", "hypercholesterolaemia"],
            "fatty_liver": [
                "metabolic dysfunction-associated steatotic liver disease",
                "non-alcoholic fatty liver disease",
            ],
        },
        "outcomes": {
            "lipids": ["cholesterol"],
        },
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["dyslipidaemia"],
                "clinical_keys": ["diabetes", "lipids", "fatty_liver"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["lipids"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["practice guidance"],
            }
        },
    }

    queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    joined = "\n".join(queries)

    assert '"Prediabetic State"[MeSH Terms]' in joined
    assert '"Insulin Resistance"[MeSH Terms]' in joined
    assert '"Dyslipidemias"[MeSH Terms]' in joined
    assert '"Hypercholesterolemia"[MeSH Terms]' in joined
    assert '"Non-alcoholic Fatty Liver Disease"[MeSH Terms]' in joined


def test_busca2b_enhancements_add_prediabetes_and_insulin_resistance_queries() -> None:
    queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert '"prediabetes"[Title/Abstract]' in joined
    assert '"insulin resistance"[Title/Abstract]' in joined


def test_busca2a_guidance_terms_pull_guideline_variants_into_queries() -> None:
    taxonomy = {
        "global": {
            "document_types": {"guidelines": ["guideline"]},
            "diet_patterns": {"core": ["mediterranean diet"]},
            "nutrition_domains": {"core": ["medical nutrition therapy"]},
            "implementation_behavior": {"adherence": ["adherence"]},
        },
        "clinical": {
            "obesity": ["obesity"],
            "diabetes": ["type 2 diabetes"],
        },
        "outcomes": {
            "metabolic": ["hba1c", "blood pressure"],
        },
        "workstreams": {
            "busca2a": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["guidelines"],
                "priority_outcomes": ["metabolic"],
                "focus_blocks": ["diet_patterns", "implementation_behavior"],
                "web_query_hints": ["clinical practice guideline"],
            }
        },
    }

    queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    joined = "\n".join(queries)

    assert '"consensus guidance"[Title/Abstract]' in joined
    assert '"best practice advice"[Title/Abstract]' in joined
    assert '"standards of care"[Title/Abstract]' in joined
    assert '"position statement"[Title/Abstract]' in joined
