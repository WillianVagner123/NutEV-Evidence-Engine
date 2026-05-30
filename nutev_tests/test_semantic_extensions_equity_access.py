from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_equity_access_extension_adds_food_environment_precision_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=4)}

    assert "food apartheid" in terms
    assert "healthy food retail" in terms
    assert "geographic food access" in terms
    assert "neighborhood food environment" in terms


def test_equity_access_extension_adds_policy_and_intervention_document_terms() -> None:
    terms = {
        term.lower()
        for term in semantic_terms(
            "busca2b",
            field="document_terms",
            min_priority=4,
        )
    }

    assert "healthy food retail intervention" in terms
    assert "food environment policy" in terms
    assert "natural experiment" in terms
