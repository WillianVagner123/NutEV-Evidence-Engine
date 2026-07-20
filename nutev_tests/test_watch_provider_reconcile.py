"""Global Watch ↔ registry reconciliation (T6): the two search stacks must agree.

Global Watch keeps its own query-building and provider-dispatch stack instead of
going through ``search.provider_orchestrator``. That duplication is tolerated,
but the two stacks must not disagree about *which* providers exist. This guard —
mirroring ``test_provider_reconcile`` for the orchestrator — fails if Global
Watch ever runs a provider the central registry never declared.
"""
from __future__ import annotations

from nutev.global_watch.watch_pipeline import watch_provider_ids
from nutev.search.provider_registry import declared_provider_ids, reconcile_providers


def test_every_watch_provider_is_declared_in_the_registry():
    rec = reconcile_providers(watch_provider_ids())
    assert rec["implemented_not_declared"] == [], (
        f"Global Watch runs providers not declared in the registry: {rec['implemented_not_declared']}"
    )


def test_watch_providers_are_the_shared_bibliographic_connectors():
    ids = set(watch_provider_ids())
    declared = declared_provider_ids()
    # Watch uses the same core bibliographic connectors as the main pipeline.
    assert {"pubmed", "europepmc", "openalex"} <= ids
    assert ids <= declared  # never a provider the registry doesn't know about
