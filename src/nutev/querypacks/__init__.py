from __future__ import annotations

from nutev.querypacks.ckm_extensions import apply_ckm_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_ckm_extensions()

__all__ = ["apply_semantic_extensions", "apply_ckm_extensions"]
