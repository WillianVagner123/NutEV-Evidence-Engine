from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.semantic_blocks import semantic_terms


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=3)}


def test_iberoamerican_guidance_terms_reach_policy_and_framework_querypacks() -> None:
    busca1_terms = _lowered_terms("busca1")
    framework_terms = _lowered_terms("artigo3_framework")

    assert "guia alimentar para a população brasileira" in busca1_terms
    assert "guías alimentarias basadas en alimentos" in busca1_terms
    assert "alimentação adequada e saudável" in busca1_terms
    assert "educación alimentaria y nutricional" in framework_terms
    assert "comensalidad" in framework_terms


def test_iberoamerican_guidance_document_terms_reach_evidence_synthesis() -> None:
    busca1_document_terms = _lowered_terms("busca1", field="document_terms")
    busca2a_document_terms = _lowered_terms("busca2a", field="document_terms")

    assert "guia alimentar para a população brasileira" in busca1_document_terms
    assert "guías alimentarias basadas en alimentos" in busca1_document_terms
    assert "recomendaciones alimentarias" in busca2a_document_terms


def test_iberoamerican_guidance_extensions_do_not_duplicate_terms() -> None:
    for block_name in (
        "evidence_synthesis",
        "food_literacy_agency",
        "commensality_context",
        "lifestyle_nutrition_patterns",
    ):
        block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS[block_name]
        assert len(block["terms"]) == len({term.lower() for term in block["terms"]})
        assert len(block["document_terms"]) == len(
            {term.lower() for term in block["document_terms"]}
        )
