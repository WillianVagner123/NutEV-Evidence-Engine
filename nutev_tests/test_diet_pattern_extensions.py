from __future__ import annotations

from nutev.querypacks.diet_pattern_extensions import (
    apply_diet_pattern_precision_extensions,
)
from nutev.querypacks.semantic_blocks import semantic_terms


def test_diet_pattern_extensions_cover_cardiometabolic_patterns() -> None:
    terms = semantic_terms("busca2b", min_priority=5)

    assert "mediterranean diet adherence" in terms
    assert "dash diet intervention" in terms
    assert "portfolio diet intervention" in terms
    assert "low glycemic index diet" in terms


def test_diet_pattern_extensions_are_idempotent() -> None:
    before = semantic_terms("busca2b", min_priority=5).count(
        "mediterranean diet adherence"
    )

    apply_diet_pattern_precision_extensions()
    after = semantic_terms("busca2b", min_priority=5).count(
        "mediterranean diet adherence"
    )

    assert before == 1
    assert after == 1
