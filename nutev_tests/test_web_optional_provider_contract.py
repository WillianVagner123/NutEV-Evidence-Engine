from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "apps" / "nutev-web"
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

MODULE_PATH = WEB_ROOT / "search_adapter.py"
SPEC = importlib.util.spec_from_file_location("nutev_web_search_adapter_optional_contract", MODULE_PATH)
assert SPEC and SPEC.loader
adapter = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = adapter
SPEC.loader.exec_module(adapter)


class _Result:
    def __init__(self, rows: list[dict[str, str]], status: str = "completed") -> None:
        self.rows = rows
        self.status = status
        self.total_found = None
        self.error = ""


def test_provider_order_includes_optional_web_sources() -> None:
    assert adapter.PROVIDER_ORDER == (
        "pubmed",
        "europepmc",
        "openalex",
        "crossref",
        "doaj",
        "semantic_scholar",
        "google_pse",
        "brave",
        "serpapi",
        "lilacs_bvs_native",
        "scielo_native",
    )
    assert adapter.LATIN_PROVIDERS == ("lilacs_bvs_native", "scielo_native")


def test_optional_web_cap_is_recorded_as_partial_when_saturated() -> None:
    result = adapter._cap_aware_optional_result(
        "brave",
        requested_limit=2_147_483_647,
        cap=20,
        call=lambda: _Result([{"title": str(index)} for index in range(20)]),
    )
    assert result.status == "partial"
    assert result.error == "connector_limit_reached:brave:20"


def test_optional_web_result_below_cap_can_remain_complete() -> None:
    result = adapter._cap_aware_optional_result(
        "brave",
        requested_limit=2_147_483_647,
        cap=20,
        call=lambda: _Result([{"title": "one"}]),
    )
    assert result.status == "completed"
    assert result.error == ""


def test_missing_credentials_status_is_not_rewritten(monkeypatch) -> None:
    result = _Result([], status="skipped")
    result.error = "missing BRAVE_API_KEY"
    monkeypatch.setattr(adapter, "search_brave", lambda query, limit: result)

    returned = adapter._provider_call("brave", "nutrition", 2_147_483_647)()

    assert returned.status == "skipped"
    assert returned.error == "missing BRAVE_API_KEY"


def test_bounded_search_records_partial_and_skipped_as_provider_gaps(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(adapter, "_read_profile", lambda: {"focus_keywords": [], "provider_weights": {}, "guardrails": {}})
    monkeypatch.setattr(adapter, "load_canonical_taxonomy", lambda path: ({}, {"primary_dimension_order": []}))
    monkeypatch.setattr(adapter, "dedupe_records", lambda rows: rows)
    monkeypatch.setattr(adapter, "_score_rows", lambda rows, query=None: rows)
    monkeypatch.setattr(adapter, "_persist_search", lambda result, output_root: None)

    skipped = _Result([], status="skipped")
    skipped.error = "missing BRAVE_API_KEY"
    partial = _Result([{"title": "x", "url": "https://example.org/x"}], status="partial")
    partial.error = "connector_limit_reached:google_pse:100"

    def fake_call(provider, query, limit):
        if provider == "brave":
            return lambda: skipped
        if provider == "google_pse":
            return lambda: partial
        raise AssertionError(provider)

    monkeypatch.setattr(adapter, "_provider_call", fake_call)
    result = adapter.search_evidence(
        "nutrition",
        providers=["google_pse", "brave"],
        per_provider=25,
        max_results=100,
        output_root=tmp_path,
    )

    assert result["status"] == "COMPLETE_WITH_PROVIDER_GAPS"
    assert result["partial_providers"] == ["google_pse"]
    assert result["skipped_providers"] == ["brave"]
