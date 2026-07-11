from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks.semantic_blocks import semantic_terms


def test_food_environment_policy_terms_extend_busca1_semantic_context() -> None:
    terms = {term.lower() for term in semantic_terms("busca1", min_priority=4)}
    document_terms = {
        term.lower()
        for term in semantic_terms("busca1", field="document_terms", min_priority=4)
    }

    assert "healthy food retail policy" in terms
    assert "food procurement policy" in terms
    assert "healthy food service guidelines" in terms
    assert "food procurement policy evaluation" in document_terms
    assert "menu labeling policy evaluation" in document_terms


def test_food_environment_policy_terms_extend_implementation_query_context() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    assert "choice architecture intervention" in terms
    assert "nutrition standards for food service" in terms
    assert "front-of-pack labeling policy" in terms
