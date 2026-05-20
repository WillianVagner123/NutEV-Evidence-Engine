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


def test_provider_queries_include_living_guideline_and_consensus_variants() -> None:
    pubmed_queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "pubmed")
    europepmc_queries = render_queries_for_provider(_sample_taxonomy(), "busca2b", "europepmc")
    pubmed_joined = "\n".join(pubmed_queries).lower()
    europepmc_joined = "\n".join(europepmc_queries).lower()

    assert "living guideline" in pubmed_joined
    assert "consensus report" in pubmed_joined
    assert "expert consensus" in pubmed_joined
    assert "clinical guidance" in pubmed_joined
    assert "practice recommendation" in pubmed_joined
    assert "living guideline" in europepmc_joined
    assert "consensus report" in europepmc_joined
    assert "expert consensus" in europepmc_joined
    assert "clinical guidance" in europepmc_joined
    assert "practice recommendation" in europepmc_joined


def test_semantic_blocks_are_prioritized_by_workstream():
    busca1_blocks = semantic_block_names("busca1")
    busca2b_terms = semantic_terms("busca2b", min_priority=5)
    priorities = prioritized_semantic_blocks("a3")

    assert busca1_blocks[:2] == ["food_literacy_agency", "commensality_context"]
    assert "implementation science" in busca2b_terms
    assert "adherence" in busca2b_terms
    assert priorities[0] == {"name": "food_literacy_agency", "priority": 5}


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
