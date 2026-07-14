"""Shared pytest fixtures/bootstrap for the canonical NutEV suite.

Apply the runtime-compat hooks deterministically before any test runs. The
suite exercises the same wrapped pipeline behaviour that a real ``nutev`` run
uses; relying on ``sitecustomize.py`` being auto-imported is fragile (it is
shadowed on distros that ship their own ``sitecustomize``), so we apply the
hooks explicitly here instead.
"""
from __future__ import annotations

try:
    from nutev.runtime_compat import apply as _apply_runtime_compat

    _apply_runtime_compat()
except Exception:
    pass
