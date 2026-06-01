from nutev.querypacks.semantic_blocks import semantic_terms


def test_official_guidance_extensions_feed_high_priority_evidence_synthesis_terms():
    terms = set(semantic_terms("busca2a", min_priority=5))
    document_terms = set(
        semantic_terms("busca2a", field="document_terms", min_priority=5)
    )

    assert "evidence-based guideline" in terms
    assert "position statement" in terms
    assert "expert consensus" in terms
    assert "clinical consensus statement" in document_terms
    assert "recommendation statement" in document_terms
