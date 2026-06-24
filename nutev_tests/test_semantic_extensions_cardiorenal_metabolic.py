from __future__ import annotations

import nutev.querypacks.semantic_extensions  # noqa: F401
from nutev.querypacks.semantic_blocks import semantic_terms


def test_cardiorenal_metabolic_terms_extend_cardiometabolic_workstreams() -> None:
    busca2a_terms = {term.lower() for term in semantic_terms("busca2a")}
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b")}

    assert "cardiorenal metabolic syndrome" in busca2a_terms
    assert "kidney-heart-metabolic risk" in busca2b_terms


def test_cardiorenal_metabolic_terms_do_not_expand_busca1_noise() -> None:
    busca1_terms = {term.lower() for term in semantic_terms("busca1")}

    assert "cardiorenal metabolic syndrome" not in busca1_terms
