"""Registry ↔ orchestrator reconciliation — the single-source-of-truth guard."""
from __future__ import annotations

from nutev.search.provider_orchestrator import implemented_search_providers
from nutev.search.provider_registry import (
    declared_provider_ids,
    reconcile_providers,
)


def test_every_implemented_provider_is_declared():
    # The audit's core concern: code runs a provider the config never declared.
    rec = reconcile_providers(implemented_search_providers())
    assert rec["implemented_not_declared"] == [], (
        f"provedores implementados mas não declarados no registry: {rec['implemented_not_declared']}"
    )


def test_aliases_bridge_config_ids_to_orchestrator_ids():
    declared = declared_provider_ids()
    # Orchestrator uses 'pubmed'/'brave'; config declares ncbi_pubmed/brave_search
    # + these aliases. Both the canonical id and the alias resolve.
    assert "pubmed" in declared and "ncbi_pubmed" in declared
    assert "brave" in declared and "brave_search" in declared
    assert "official_web" in declared and "official_sources" in declared


def test_reconcile_flags_a_fake_undeclared_provider():
    rec = reconcile_providers([*implemented_search_providers(), "totally_made_up"])
    assert "totally_made_up" in rec["implemented_not_declared"]
