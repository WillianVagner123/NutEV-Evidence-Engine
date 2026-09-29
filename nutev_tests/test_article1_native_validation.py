from __future__ import annotations

import json
from pathlib import Path

from nutev.science.article1_press import FORMAL_PROVIDERS, ROUTE_ORDER, compile_route_query, route_specs


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "config" / "nutev" / "article1_query_draft_v1.json"
PRESS = ROOT / "config" / "nutev" / "article1_press_review_v1.json"
RUNNER = ROOT / "tools" / "run_article1_native_validation.py"


def test_formal_provider_set_is_exactly_available_sources() -> None:
    assert FORMAL_PROVIDERS == ("pubmed", "lilacs_bvs", "scielo")


def test_every_native_provider_compiles_every_article1_route() -> None:
    draft = json.loads(DRAFT.read_text(encoding="utf-8"))
    specs = route_specs(draft)
    for provider in FORMAL_PROVIDERS:
        for route_id in ROUTE_ORDER:
            assert compile_route_query(provider, specs[route_id]).strip()


def test_press_registry_marks_unavailable_licensed_sources_as_excluded() -> None:
    press = json.loads(PRESS.read_text(encoding="utf-8"))
    registry = press["provider_native_validation"]
    for provider in ("scopus", "web_of_science"):
        assert registry[provider]["role"] == "excluded_unavailable_provider"
        assert registry[provider]["status"] == "NO_ACCESS_NOT_IN_FORMAL_SET"
        assert registry[provider]["simulation_forbidden"] is True


def test_native_validation_runner_is_fail_closed() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert "choices=FORMAL_PROVIDERS" in source
    assert '"formal_search_performed": False' in source
    assert '"prisma_event_emitted": False' in source
    assert '"eligibility_decisions_created": False' in source
    assert '"human_review_required_before_gate_change": True' in source
