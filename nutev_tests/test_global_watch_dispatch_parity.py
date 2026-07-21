"""Phase-0 parity harness for the global_watch unification.

Gate for `docs/REFACTOR_GLOBAL_WATCH_UNIFICATION.md`. Two things:

1. **Baseline lock** — `run_watch_provider`'s dispatch → normalized-hits output
   per provider (from fixed input rows) is pinned as a committed digest. Phase 1
   (routing dispatch through `search.provider_orchestrator.search_provider`) must
   keep these digests for the shared-connector providers.
2. **Unification equivalence** — proves that for europepmc/openalex/crossref the
   orchestrator's registry function, called with Watch's per-provider cap, makes
   the *identical* underlying connector call the Watch stack makes today. That is
   the green light for Phase 1 on those three providers.

pubmed is deliberately excluded from (2): the orchestrator runs it through
`PubMedClient().search(...)` while Watch calls `search_pubmed(q, retmax=12)` — a
different implementation. Unifying pubmed dispatch would change results, so it is
a product decision (see the plan), not part of Phase 1.
"""
from __future__ import annotations

import hashlib
import json
import logging
import tempfile
from pathlib import Path

import nutev.global_watch.watch_pipeline as wp

_BASELINE = Path(__file__).parent / "parity" / "global_watch_dispatch_baseline.json"

PROVIDERS = ["pubmed", "europepmc", "openalex", "crossref"]
_CONNECTOR_FNS = ["search_pubmed", "search_europepmc", "search_openalex", "search_crossref"]

# Same fixed rows used to generate the committed baseline.
FIXED = [
    {"title": "Clinical practice guideline for obesity and cardiometabolic care", "url": "https://x.org/a", "doi": "10.1/a", "pmid": "111", "year": 2026, "abstract": "guideline text", "journal": "J Nutr", "authors": "Silva J"},
    {"title": "Mediterranean dietary pattern and cardiometabolic outcomes: a review", "url": "https://x.org/b", "doi": "10.1/b", "year": 2025, "snippet": "systematic review", "journal": "Nutr Rev"},
    {"title": "Food environment intervention and diet quality", "url": "https://x.org/c", "year": 2024},
]

# Watch's per-provider caps (from watch_pipeline._build_provider_map) and the
# orchestrator kwarg each maps to.
_SHARED = {
    "europepmc": ("search_europepmc", "page_size", 12),
    "openalex": ("search_openalex", "per_page", 10),
    "crossref": ("search_crossref", "rows", 10),
}


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def _dispatch(provider: str, monkeypatch) -> list[dict]:
    # Mock the connector on BOTH bindings — the watch module and the orchestrator —
    # so the gate holds whether dispatch calls the connector directly (pre-Phase 1)
    # or through the orchestrator registry (post-Phase 1). Same rows in, so the
    # normalized-hits digest must be identical either way.
    import nutev.search.provider_orchestrator as po

    for name in _CONNECTOR_FNS:
        monkeypatch.setattr(wp, name, lambda *a, **k: list(FIXED), raising=False)
        monkeypatch.setattr(po, name, lambda *a, **k: list(FIXED), raising=False)
    logs = Path(tempfile.mkdtemp())
    return wp.run_watch_provider(provider, "diet adherence", "guidelines_consensus", logging.getLogger("t"), "run", logs, 30)


def test_watch_dispatch_matches_baseline(monkeypatch):
    baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
    for provider in PROVIDERS:
        hits = _dispatch(provider, monkeypatch)
        assert _sha(hits) == baseline["by_provider"][provider]["sha256"], f"watch dispatch drifted: {provider}"
        assert len(hits) == baseline["by_provider"][provider]["n_hits"]


def test_shared_connectors_are_unified_through_the_orchestrator(monkeypatch):
    # Post-Phase-1: the watch provider map delegates europepmc/openalex/crossref to
    # the orchestrator registry, so the watch entry point and the registry make the
    # identical underlying connector call with Watch's cap.
    import nutev.search.provider_orchestrator as po

    for provider, (fn_name, kwarg, cap) in _SHARED.items():
        calls: list[dict] = []

        def spy(*args, **kwargs):
            calls.append({"args": args, "kwargs": dict(kwargs)})
            return [{"title": "X", "url": "https://x", "year": 2026}]

        monkeypatch.setattr(po, fn_name, spy)  # the shared binding both paths now use

        watch_rows = wp._build_provider_map()[provider]("q")  # watch → registry → spy
        watch_call = calls[-1]
        calls.clear()
        orch_rows = po._registry()[provider]("q", cap, {})     # registry directly → spy
        orch_call = calls[-1]

        assert watch_rows == orch_rows, f"{provider}: rows differ"
        assert watch_call == orch_call == {"args": ("q",), "kwargs": {kwarg: cap}}, (
            f"{provider}: watch vs orchestrator connector call differs: {watch_call} != {orch_call}"
        )


def test_pubmed_dispatch_diverges_and_is_out_of_phase1_scope():
    # The watch runs pubmed via the module function; the orchestrator via a client
    # class. They are different implementations, so pubmed is NOT unified in Phase 1.
    from nutev.search.provider_orchestrator import _registry

    assert "pubmed" not in _registry()  # orchestrator special-cases pubmed (PubMedClient)
    assert "pubmed" in wp._build_provider_map()  # watch uses search_pubmed directly
