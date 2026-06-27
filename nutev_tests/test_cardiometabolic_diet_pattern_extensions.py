from __future__ import annotations

from nutev.querypacks.semantic_blocks import (
    prioritized_semantic_blocks,
    semantic_terms,
)


def test_cardiometabolic_diet_patterns_prioritize_busca2b_terms() -> None:
    terms = semantic_terms("busca2b", min_priority=5)
    document_terms = semantic_terms("busca2b", field="document_terms", min_priority=5)

    assert "portfolio diet for dyslipidemia" in terms
    assert "heart-healthy dietary pattern" in terms
    assert "portfolio diet intervention trial" in document_terms


def test_cardiometabolic_diet_patterns_support_guideline_workstream() -> None:
    terms = semantic_terms("busca2a", min_priority=4)
    document_terms = semantic_terms("busca2a", field="document_terms", min_priority=4)

    assert "dash diet for hypertension" in terms
    assert "low-sodium diet guideline" in document_terms


def test_cardiometabolic_diet_patterns_are_lower_priority_for_busca1() -> None:
    priorities = prioritized_semantic_blocks("busca1")
    priority_by_block = {item["name"]: item["priority"] for item in priorities}

    assert priority_by_block["cardiometabolic_diet_patterns"] == 3
    assert "portfolio diet for dyslipidemia" not in semantic_terms("busca1", min_priority=4)
