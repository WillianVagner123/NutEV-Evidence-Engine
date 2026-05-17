from pathlib import Path

from nutev.querypacks.provider_queries import (
    build_provider_querypack,
    render_queries_for_provider,
    write_provider_querypack_audit,
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
            }
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

    assert (tmp_path / "provider_querypack_executed.json").exists()
    assert (tmp_path / "provider_querypack_executed.csv").exists()