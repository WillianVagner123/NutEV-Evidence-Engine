from __future__ import annotations

"""Runtime compatibility hooks for NutEV/NutMEV local executions.

These hooks wrap a handful of pipeline functions (curation, run-summary,
synthesis defaults, query generation, workstream validation) so that a local
run emits the full audit/legacy artifact set. They MUST be applied
deterministically: call :func:`apply` from an explicit entrypoint (the ``nutev``
CLI does this) instead of relying on ``sitecustomize.py`` being auto-imported,
which only happens when no other ``sitecustomize`` shadows it on ``sys.path``.
Every patch is idempotent, so calling :func:`apply` more than once is safe.
"""

from pathlib import Path


def _patch_workstream_validation() -> None:
    try:
        from nutev.engine import models as models_module
        from nutev.engine import validators as validators_module
    except Exception:
        return
    original = getattr(validators_module, "validate_workstream", None)
    if original is None or getattr(original, "_nutev_global_watch_patched", False):
        return

    def wrapped(value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip()
        if normalized == "global_watch":
            return normalized
        return original(value)

    wrapped._nutev_global_watch_patched = True  # type: ignore[attr-defined]
    validators_module.validate_workstream = wrapped
    models_module.validate_workstream = wrapped


def _patch_synthesis_defaults() -> None:
    try:
        from nutev.analysis import synthesis as synthesis_module
    except Exception:
        return
    original = getattr(synthesis_module, "write_synthesis_outputs", None)
    if original is None or getattr(original, "_nutev_defaults_patched", False):
        return
    defaults = {"evidence_priority_score": 0, "evidence_priority_tier": "unclassified", "evidence_use_track": "unclassified", "evidence_use_primary": "", "evidence_use_secondary": "", "reading_lane": "standard"}

    def wrapped(master_rows: list[dict], out_dir: Path) -> None:
        return original([{**defaults, **dict(row)} for row in master_rows], out_dir)

    wrapped._nutev_defaults_patched = True  # type: ignore[attr-defined]
    synthesis_module.write_synthesis_outputs = wrapped


_APPLIED = False


def apply() -> None:
    """Apply all runtime-compat patches once. Idempotent and side-effect safe."""
    global _APPLIED
    if _APPLIED:
        return
    _patch_workstream_validation()
    _patch_synthesis_defaults()
    # Removed in the runtime_compat migration (docs/REFACTOR_RUNTIME_COMPAT_MIGRATION.md):
    #  - Phase 1: _patch_query_generation — query terms now native in nutev.querypacks
    #    (builders.EXTRA_BOOLEAN_QUERIES + provider_queries.PUBMED_WORKSTREAM_ANCHOR_TERMS).
    #  - Phase 2: _patch_curation / _patch_run_summary — the audit + legacy finalization
    #    is now a first-class pipeline step (nutev.export.curation_finalize).
    _APPLIED = True
