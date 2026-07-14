from __future__ import annotations

"""Backward-compatible auto-load shim for NutEV/NutMEV runtime hooks.

Python's ``site`` module auto-imports a top-level ``sitecustomize`` at
interpreter startup *when one is discoverable before any other* on
``sys.path``. That is fragile — a distro- or venv-provided ``sitecustomize``
shadows this file, silently skipping the hooks and changing pipeline outputs.

The real logic now lives in :mod:`nutev.runtime_compat` and is applied
explicitly by the ``nutev`` CLI, so behaviour is deterministic regardless of
whether this shim loads. This file is kept only so environments that *do*
auto-import it still get the same (idempotent) patches.
"""

try:
    from nutev.runtime_compat import apply as _apply

    _apply()
except Exception:
    # Never let a compatibility shim break interpreter startup.
    pass
