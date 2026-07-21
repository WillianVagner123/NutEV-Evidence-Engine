"""The Article-1 search workstreams must keep DOAJ and SciELO as default,
dispatchable sources (methodology changelog 2026-07-21). This locks the
config + dispatch wiring together so a future edit to keyword_taxonomy.json
or the provider map can't silently drop them from the default run.
"""
from __future__ import annotations

import json
from pathlib import Path

from nutev.pipelines.master_pipeline import _provider_map, _split_supported_providers

_WORKSTREAMS = ("busca1", "busca2a", "busca2b", "artigo3_framework")
_DEFAULT_BIBLIOGRAPHIC = ("doaj", "scielo")


def _taxonomy() -> dict:
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / "config" / "keyword_taxonomy.json").read_text(encoding="utf-8"))


def test_default_workstreams_declare_and_support_doaj_and_scielo():
    taxonomy = _taxonomy()
    provider_map = _provider_map()
    workstreams = taxonomy.get("workstreams", {})
    for ws in _WORKSTREAMS:
        priority = workstreams[ws].get("source_priority", [])
        supported, _ = _split_supported_providers(priority, provider_map)
        for provider in _DEFAULT_BIBLIOGRAPHIC:
            assert provider in priority, f"{ws} no longer declares {provider}"
            assert provider in supported, f"{ws} declares {provider} but it is not dispatchable"


def test_default_workstreams_declare_no_phantom_providers():
    """Every provider a default workstream declares must be dispatchable — no
    phantom entries (e.g. the removed google_cse/ddg_web) that log 'unsupported'
    and silently do nothing on every run."""
    taxonomy = _taxonomy()
    provider_map = _provider_map()
    workstreams = taxonomy.get("workstreams", {})
    for ws in _WORKSTREAMS:
        priority = workstreams[ws].get("source_priority", [])
        _, unsupported = _split_supported_providers(priority, provider_map)
        assert unsupported == [], f"{ws} declares undispatchable providers: {unsupported}"
