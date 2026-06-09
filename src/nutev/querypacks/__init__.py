from __future__ import annotations

from nutev.querypacks.semantic_extensions import apply_semantic_extensions
from nutev.querypacks.therapeutic_diet_extensions import apply_therapeutic_diet_extensions

apply_semantic_extensions()
apply_therapeutic_diet_extensions()

__all__ = ["apply_semantic_extensions", "apply_therapeutic_diet_extensions"]
