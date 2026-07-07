from __future__ import annotations

from nutev.querypacks import semantic_blocks


def test_ckm_nutrition_terms_are_loaded_into_semantic_blocks() -> None:
    cardiometabolic_terms = {
        term.lower()
        for term in semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["cardiometabolic_precision"]["terms"]
    }
    synthesis_document_terms = {
        term.lower()
        for term in semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["evidence_synthesis"]["document_terms"]
    }

    assert "ckm syndrome nutrition therapy" in cardiometabolic_terms
    assert "ckm syndrome dietary guideline" in synthesis_document_terms
