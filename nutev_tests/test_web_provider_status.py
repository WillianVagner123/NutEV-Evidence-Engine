"""Hosted search: a connector failure is reported as a failure, never as "no results".

Audit finding A8 (docs/SEARCH_KEYWORD_AUDIT_2026-10.md): the legacy list helpers
collapse a remote failure into an empty list, which the web path used to record as
"empty". The web path now calls the status-aware discovery adapters.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from nutev.search import crossref as crossref_mod
from nutev.search import europepmc as europepmc_mod
from nutev.search import openalex as openalex_mod
from nutev.search.status_adapters import STATUS_AWARE_DISCOVERY_CLIENTS

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "apps" / "nutev-web"
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

MODULE_PATH = WEB_ROOT / "search_adapter.py"
SPEC = importlib.util.spec_from_file_location("nutev_web_search_adapter_status", MODULE_PATH)
assert SPEC and SPEC.loader
adapter = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = adapter
SPEC.loader.exec_module(adapter)

FAILING_GETTERS = {
    "europepmc": (europepmc_mod, "_europepmc_get"),
    "openalex": (openalex_mod, "_openalex_get"),
    "crossref": (crossref_mod, "_crossref_get"),
}


def test_every_status_aware_provider_is_used_by_the_web_path() -> None:
    for provider in STATUS_AWARE_DISCOVERY_CLIENTS:
        assert provider in adapter.DIRECT_PROVIDERS
        call = adapter._provider_call(provider, "mediterranean diet", 5)
        assert callable(call)
    source = MODULE_PATH.read_text(encoding="utf-8")
    for legacy in ("search_europepmc(", "search_openalex(", "search_crossref(", "search_doaj(", "search_semantic_scholar("):
        assert legacy not in source, legacy


@pytest.mark.parametrize("provider", sorted(FAILING_GETTERS))
def test_remote_failure_is_failed_not_empty(monkeypatch: pytest.MonkeyPatch, provider: str) -> None:
    module, getter = FAILING_GETTERS[provider]
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(module, getter, lambda *_args, **_kwargs: None)
    raw = adapter._provider_call(provider, "mediterranean diet", 5)()
    rows, status, _total, error = adapter._normalize_provider_result(raw)
    assert rows == []
    assert status == "failed"
    assert error


def test_successful_zero_hit_search_is_not_a_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(
        europepmc_mod,
        "_europepmc_get",
        lambda *_args, **_kwargs: {"hitCount": 0, "resultList": {"result": []}},
    )
    rows, status, total, _error = adapter._normalize_provider_result(
        adapter._provider_call("europepmc", "zzzz no hits", 5)()
    )
    # "empty" now means what it says: the source answered and had nothing.
    assert rows == [] and status == "empty" and total == 0
