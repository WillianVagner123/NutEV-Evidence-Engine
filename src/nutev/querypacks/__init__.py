from __future__ import annotations

from nutev.querypacks.diet_quality_extensions import apply_diet_quality_extensions
from nutev.querypacks.food_access_extensions import apply_food_access_benefit_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_food_access_benefit_extensions()
apply_diet_quality_extensions()

__all__ = [
    "apply_diet_quality_extensions",
    "apply_food_access_benefit_extensions",
    "apply_semantic_extensions",
]
