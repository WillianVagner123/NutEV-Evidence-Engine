from __future__ import annotations

import pytest

from nutev.global_watch.watch_query_builder import build_watch_queries


@pytest.mark.xfail(
    reason=(
        "Global Watch quick mode currently interleaves category seeds before "
        "the Food is Medicine lifestyle seed group, so high-value food access "
        "program terms can fall outside the first query budget."
    ),
    strict=False,
)
def test_default_quick_watch_budget_includes_food_access_program_terms() -> None:
    queries = build_watch_queries(None, since_days=7, mode="quick")[:8]
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert "food is medicine" in rendered
    assert "produce prescription" in rendered
    assert "medically tailored meal" in rendered
