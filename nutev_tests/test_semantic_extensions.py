from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.querypacks.semantic_extensions import apply_semantic_extensions


def test_remission_terms_reach_cardiometabolic_workstreams() -> None:
    apply_semantic_extensions()

    busca2a_terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}
    busca2b_terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}

    assert "type 2 diabetes remission" in busca2a_terms
    assert "weight regain prevention" in busca2b_terms


def test_remission_extension_is_idempotent() -> None:
    apply_semantic_extensions()
    before = semantic_terms("busca2b", min_priority=5).count("type 2 diabetes remission")

    apply_semantic_extensions()
    after = semantic_terms("busca2b", min_priority=5).count("type 2 diabetes remission")

    assert before == 1
    assert after == 1
