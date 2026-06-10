from __future__ import annotations

from nutev.querypacks.food_environment_policy_extensions import (
    apply_food_environment_policy_extensions,
)
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_food_environment_policy_extensions()

__all__ = ["apply_food_environment_policy_extensions", "apply_semantic_extensions"]
