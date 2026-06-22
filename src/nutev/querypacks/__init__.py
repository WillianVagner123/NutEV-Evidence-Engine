from __future__ import annotations

from nutev.querypacks.ckm_extensions import apply_ckm_extensions
from nutev.querypacks.food_access_extensions import apply_food_access_benefit_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_food_access_benefit_extensions()
apply_ckm_extensions()

__all__ = [
    "apply_ckm_extensions",
    "apply_food_access_benefit_extensions",
    "apply_semantic_extensions",
]
