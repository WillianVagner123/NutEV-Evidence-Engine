from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks.semantic_blocks import semantic_terms
from nutev.querypacks.semantic_extensions import BEHAVIOR_CHANGE_PLANNING_TERMS


def test_busca2b_includes_behavior_change_planning_terms() -> None:
    terms = " ".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "implementation intention" in terms
    assert "habit formation" in terms
    assert "action planning" in terms
    assert "coping planning" in terms


def test_artigo3_includes_behavior_change_planning_terms() -> None:
    terms = " ".join(semantic_terms("artigo3_framework", min_priority=4)).lower()

    assert "implementation intentions" in terms
    assert "goal setting" in terms
    assert "self-regulation" in terms


def test_behavior_change_planning_terms_are_unique_case_insensitive() -> None:
    lowered = [term.lower() for term in BEHAVIOR_CHANGE_PLANNING_TERMS]

    assert len(lowered) == len(set(lowered))
