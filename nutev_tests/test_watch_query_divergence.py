"""Global Watch keeps its own query builder — an intentional, documented divergence.

Phase 3 of docs/REFACTOR_GLOBAL_WATCH_UNIFICATION.md was evaluated and DECLINED:
the Watch's category-based surveillance queries and the pipeline's workstream-based
review queries are organized on different axes and are not redundant. This test
pins that decision so a future change to merge the two query systems is a
deliberate, reviewed act (it would have to change these assertions), not an
accidental one.
"""
from __future__ import annotations


def test_watch_and_pipeline_query_builders_are_organized_differently():
    from nutev.global_watch.watch_config import WATCH_CATEGORIES
    from nutev.querypacks.builders import canonical_workstream

    # Watch is organized by surveillance category; the pipeline by review workstream.
    watch_categories = set(WATCH_CATEGORIES)
    pipeline_workstreams = {canonical_workstream(w) for w in ("busca1", "busca2a", "busca2b", "a3")}

    assert len(watch_categories) >= 8
    # No category IS a workstream — the two axes are disjoint, so there is no
    # 1:1 mapping to unify against.
    assert watch_categories.isdisjoint(pipeline_workstreams)


def test_watch_query_builder_is_still_the_watch_query_source():
    # The Watch still builds its own queries (not delegated to querypacks/strategy).
    from nutev.global_watch.watch_query_builder import build_watch_queries

    queries = build_watch_queries([], since_days=7, mode="quick")
    assert queries, "watch must produce its own surveillance queries"
    assert all("category" in q for q in queries)  # category-based, by design
