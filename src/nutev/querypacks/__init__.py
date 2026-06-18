from __future__ import annotations

from nutev.querypacks.behavior_maintenance_extensions import (
    apply_behavior_maintenance_extensions,
)
from nutev.querypacks.food_access_extensions import apply_food_access_benefit_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_food_access_benefit_extensions()
apply_behavior_maintenance_extensions()

__all__ = [
    "apply_behavior_maintenance_extensions",
    "apply_food_access_benefit_extensions",
    "apply_semantic_extensions",
]
