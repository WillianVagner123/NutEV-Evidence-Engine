"""Shared pytest bootstrap for the canonical NutEV suite.

The former ``runtime_compat`` shim was fully dissolved into first-class code
(see ``docs/REFACTOR_RUNTIME_COMPAT_MIGRATION.md``), so there is no longer any
hook to apply before the suite runs — the pipeline behaves the same whether or
not anything is bootstrapped here.
"""
from __future__ import annotations
