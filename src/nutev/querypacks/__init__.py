from __future__ import annotations

from nutev.querypacks.hepatic_steatosis_extensions import apply_hepatic_steatosis_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_hepatic_steatosis_extensions()

__all__ = [
    "apply_hepatic_steatosis_extensions",
    "apply_semantic_extensions",
]
