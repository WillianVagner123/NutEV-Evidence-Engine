"""The master pipeline must honor providers a workstream opts into via
source_priority. _provider_map() is derived from the orchestrator's implemented
registry, so a declared+wired connector (doaj/clinicaltrials/scielo/
semantic_scholar/arxiv) is classified 'supported' — not silently dropped — while
default runs are unchanged (DEFAULT_PRIORITY still lists only the always-on
scientific providers).
"""
from __future__ import annotations

from nutev.pipelines.master_pipeline import (
    DEFAULT_PRIORITY,
    _provider_map,
    _split_supported_providers,
)
from nutev.search.provider_orchestrator import implemented_search_providers


def test_provider_map_matches_orchestrator_registry():
    assert set(_provider_map()) == set(implemented_search_providers())


def test_default_priority_stays_supported():
    supported, unsupported = _split_supported_providers(DEFAULT_PRIORITY, _provider_map())
    assert supported == DEFAULT_PRIORITY
    assert unsupported == []


def test_new_connectors_are_dispatchable_when_opted_in():
    priority = ["pubmed", "doaj", "clinicaltrials", "scielo", "semantic_scholar", "arxiv", "official_web"]
    supported, unsupported = _split_supported_providers(priority, _provider_map())
    assert unsupported == []
    for pid in ("doaj", "clinicaltrials", "scielo", "semantic_scholar", "arxiv"):
        assert pid in supported


def test_unknown_provider_still_reported_unsupported():
    supported, unsupported = _split_supported_providers(["pubmed", "not_a_provider"], _provider_map())
    assert supported == ["pubmed"]
    assert unsupported == ["not_a_provider"]
