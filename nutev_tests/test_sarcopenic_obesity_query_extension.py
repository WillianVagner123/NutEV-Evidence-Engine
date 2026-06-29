from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks import semantic_blocks


def test_sarcopenic_obesity_terms_extend_clinical_query_blocks() -> None:
    expected_terms = {
        "sarcopenic obesity",
        "protein intake and obesity",
        "combined diet and resistance training obesity",
    }
    expected_document_terms = {
        "sarcopenic obesity systematic review",
        "protein supplementation obesity trial",
        "combined diet and resistance training trial",
    }

    for block_name in (
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
        "nutrition_care_delivery",
        "adherence_persistence",
        "sarcopenic_obesity_nutrition",
    ):
        block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name]
        assert expected_terms.issubset(set(block["terms"]))
        assert expected_document_terms.issubset(set(block["document_terms"]))


def test_sarcopenic_obesity_block_is_prioritized_for_clinical_workstreams() -> None:
    busca2a_priorities = dict(semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES["busca2a"])
    busca2b_priorities = dict(semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES["busca2b"])

    assert busca2a_priorities["sarcopenic_obesity_nutrition"] == 4
    assert busca2b_priorities["sarcopenic_obesity_nutrition"] == 5
