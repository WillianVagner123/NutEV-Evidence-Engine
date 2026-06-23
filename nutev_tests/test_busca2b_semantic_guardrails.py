from __future__ import annotations

from nutev.querypacks.semantic_blocks import (
    prioritized_semantic_blocks,
    semantic_block_names,
    semantic_terms,
)


def test_busca2b_keeps_high_priority_semantic_blocks() -> None:
    blocks = semantic_block_names("busca2b")

    expected_blocks = {
        "cardiometabolic_liver",
        "cardiometabolic_precision",
        "nutrition_care_delivery",
        "implementation_science",
        "adherence_persistence",
        "evidence_synthesis",
        "lifestyle_nutrition_patterns",
    }

    assert expected_blocks.issubset(set(blocks))


def test_busca2b_high_priority_terms_cover_core_nutmev_axes() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    expected_terms = {
        "medical nutrition therapy",
        "dietary adherence",
        "weight loss maintenance",
        "weight regain prevention",
        "implementation outcomes",
        "cardiometabolic risk",
        "type 2 diabetes remission",
        "masld",
        "mash",
        "steatotic liver disease",
        "systematic review",
        "umbrella review",
    }

    assert expected_terms.issubset(terms)


def test_busca2b_document_terms_keep_precision_anchors() -> None:
    document_terms = {
        term.lower()
        for term in semantic_terms("busca2b", field="document_terms", min_priority=5)
    }

    expected_document_terms = {
        "clinical practice guideline",
        "systematic review",
        "meta-analysis",
        "umbrella review",
        "dietary adherence intervention",
        "weight loss maintenance trial",
        "diabetes remission guideline",
        "medical nutrition therapy guideline",
        "implementation trial",
    }

    assert expected_document_terms.issubset(document_terms)


def test_busca2b_semantic_priorities_remain_focused() -> None:
    priorities = {
        str(block["name"]): int(block["priority"])
        for block in prioritized_semantic_blocks("busca2b")
    }

    assert priorities["commensality_context"] < priorities["adherence_persistence"]
    assert priorities["food_literacy_agency"] < priorities["cardiometabolic_precision"]
