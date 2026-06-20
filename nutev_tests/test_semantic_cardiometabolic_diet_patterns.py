from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_cardiometabolic_diet_pattern_terms_feed_clinical_workstreams() -> None:
    busca2a_terms = set(semantic_terms("busca2a", min_priority=4))
    busca2b_terms = set(semantic_terms("busca2b", min_priority=5))

    expected_terms = {
        "cardiometabolic dietary pattern",
        "dash dietary pattern",
        "mediterranean-style diet",
        "portfolio dietary pattern",
        "low-glycemic index diet",
        "dietary sodium reduction",
    }

    assert expected_terms <= busca2a_terms
    assert expected_terms <= busca2b_terms


def test_cardiometabolic_diet_pattern_document_terms_are_prioritized() -> None:
    busca2b_doc_terms = set(
        semantic_terms("busca2b", field="document_terms", min_priority=5)
    )

    assert "dietary pattern guideline" in busca2b_doc_terms
    assert "dietary pattern systematic review" in busca2b_doc_terms
    assert "nutrition consensus statement" in busca2b_doc_terms
