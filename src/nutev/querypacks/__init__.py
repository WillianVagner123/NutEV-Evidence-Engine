from __future__ import annotations

from nutev.querypacks.food_access_extensions import apply_food_access_benefit_extensions
from nutev.querypacks.lifestyle_medicine_extensions import apply_lifestyle_medicine_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_food_access_benefit_extensions()
apply_lifestyle_medicine_extensions()

__all__ = [
    "apply_food_access_benefit_extensions",
    "apply_lifestyle_medicine_extensions",
    "apply_semantic_extensions",
]
