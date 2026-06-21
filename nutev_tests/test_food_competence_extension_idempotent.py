from __future__ import annotations

from nutev.querypacks.food_competence_extensions import apply_food_competence_extensions
from nutev.querypacks.semantic_blocks import semantic_terms


def test_food_competence_extension_is_idempotent() -> None:
    apply_food_competence_extensions()
    apply_food_competence_extensions()

    terms = semantic_terms("artigo3_framework", min_priority=5)

    assert terms.count("food competence") == 1
    assert terms.count("meal planning self-efficacy") == 1
