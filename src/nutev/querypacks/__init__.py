from __future__ import annotations

from nutev.querypacks.adherence_behavior_extensions import (
    apply_adherence_behavior_extensions,
)
from nutev.querypacks.carbohydrate_quality_extensions import (
    apply_carbohydrate_quality_extensions,
)
from nutev.querypacks.food_access_extensions import apply_food_access_benefit_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_carbohydrate_quality_extensions()
apply_food_access_benefit_extensions()
apply_adherence_behavior_extensions()

__all__ = [
    "apply_adherence_behavior_extensions",
    "apply_carbohydrate_quality_extensions",
    "apply_food_access_benefit_extensions",
    "apply_semantic_extensions",
]
