from __future__ import annotations

from nutev.querypacks.semantic_extensions import apply_semantic_extensions
from nutev.querypacks.nutrition_prescription_extensions import (
    apply_nutrition_prescription_extensions,
)

apply_semantic_extensions()
apply_nutrition_prescription_extensions()

__all__ = ["apply_semantic_extensions", "apply_nutrition_prescription_extensions"]
