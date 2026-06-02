from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_weight_maintenance_terms_extend_busca2b_semantic_blocks() -> None:
    terms = semantic_terms("busca2b")
    document_terms = semantic_terms("busca2b", field="document_terms")

    assert "weight regain prevention" in terms
    assert "prevention of weight regain" in terms
    assert "long-term weight loss maintenance" in terms
    assert "weight regain prevention trial" in document_terms
    assert "relapse prevention intervention" in document_terms
