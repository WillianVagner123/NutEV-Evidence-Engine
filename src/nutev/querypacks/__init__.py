from __future__ import annotations

from nutev.querypacks.nutrition_care_extensions import apply_nutrition_care_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_nutrition_care_extensions()

__all__ = ["apply_semantic_extensions", "apply_nutrition_care_extensions"]
