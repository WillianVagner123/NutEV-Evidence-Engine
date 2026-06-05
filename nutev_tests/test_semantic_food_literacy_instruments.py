from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_a3_semantic_terms_include_food_literacy_instruments() -> None:
    terms = semantic_terms("a3", min_priority=5)
    document_terms = semantic_terms("a3", field="document_terms", min_priority=5)

    assert "brief dietary assessment" in terms
    assert "dietary self-efficacy" in terms
    assert "rapid eating assessment for participants" in document_terms
    assert "dietary assessment tool validation" in document_terms
