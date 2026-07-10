from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2b_semantic_terms_include_behavioural_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b")}

    assert "behavioural lifestyle intervention" in terms
    assert "behavioural nutrition intervention" in terms
    assert "behaviour change maintenance" in terms


def test_a3_semantic_terms_include_behaviour_change_document_language() -> None:
    document_terms = {
        term.lower()
        for term in semantic_terms("artigo3_framework", field="document_terms")
    }

    assert "behaviour change intervention" in document_terms
    assert "dietary behaviour change intervention" in document_terms
