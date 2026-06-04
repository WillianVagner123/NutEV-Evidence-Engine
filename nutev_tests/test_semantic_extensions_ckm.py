from __future__ import annotations

from nutev.querypacks import semantic_blocks


def test_ckm_cardiorenal_terms_extend_cardiometabolic_precision_block() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["cardiometabolic_precision"]

    assert "cardiovascular-kidney-metabolic syndrome" in block["terms"]
    assert "cardiorenal metabolic syndrome" in block["terms"]
    assert "cardiorenal-metabolic risk" in block["terms"]
    assert "kidney cardiometabolic risk" in block["terms"]
    assert "presidential advisory" in block["document_terms"]
    assert "advisory statement" in block["document_terms"]
    assert "consensus report" in block["document_terms"]

    normalized_terms = [term.lower() for term in block["terms"]]
    assert len(normalized_terms) == len(set(normalized_terms))
