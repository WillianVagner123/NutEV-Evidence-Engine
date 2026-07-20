"""Cardiometabolic/food-environment query terms are generated natively.

Phase 1 of docs/REFACTOR_RUNTIME_COMPAT_MIGRATION.md moved these terms out of the
`runtime_compat._patch_query_generation` monkey-patch into `nutev.querypacks`.
This test now checks they live in the querypack code and are actually emitted by
the builders — and that the monkey-patch is gone.
"""
from __future__ import annotations

from nutev.querypacks.builders import EXTRA_BOOLEAN_QUERIES, build_queries
from nutev.querypacks.provider_queries import PUBMED_WORKSTREAM_ANCHOR_TERMS


def test_pubmed_anchor_terms_are_declared_natively() -> None:
    expected_terms = [
        "DASH eating plan",
        "TLC diet",
        "therapeutic lifestyle changes diet",
        "heart-healthy diet",
        "cardioprotective diet",
        "diet quality",
        "healthy eating pattern",
    ]
    busca2b = PUBMED_WORKSTREAM_ANCHOR_TERMS["busca2b"]
    for term in expected_terms:
        assert term in busca2b


def test_extra_boolean_queries_cover_cardiometabolic_conditions() -> None:
    joined = " ".join(EXTRA_BOOLEAN_QUERIES["busca2b"])
    assert "type 2 diabetes" in joined
    assert "dyslipidemia" in joined
    assert "food is medicine" in joined


def test_build_queries_emits_the_food_medicine_query() -> None:
    # End-to-end: the native builder actually emits the moved boolean query.
    taxonomy = {"workstreams": {"busca2b": {"population_terms": ["adults"], "condition_terms": ["obesity"]}}}
    queries = build_queries(taxonomy, "busca2b")
    assert any("food is medicine" in q for q in queries)


def test_query_generation_monkeypatch_is_removed() -> None:
    import importlib.util

    # The runtime_compat shim (and its query-generation patch) is gone entirely;
    # the terms now live in nutev.querypacks (asserted above).
    assert importlib.util.find_spec("nutev.runtime_compat") is None
