from __future__ import annotations

import importlib

from nutev.global_watch.watch_query_builder import build_watch_queries


def _render_watch_queries(category: str, mode: str = "quick") -> str:
    queries = build_watch_queries([category], since_days=30, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def _score_watch_item(item: dict) -> float:
    module = importlib.import_module("nutev.global_watch.watch_scoring")
    return module.score_watch_item(item)


def test_group_visit_terms_render_in_lifestyle_watch_queries() -> None:
    rendered = _render_watch_queries("lifestyle_medicine")

    assert "shared medical appointment nutrition" in rendered
    assert "group medical visit diabetes" in rendered
    assert "lifestyle medicine group visit" in rendered


def test_group_visit_terms_improve_watch_priority() -> None:
    assert _score_watch_item(
        {
            "title": (
                "Shared medical appointment nutrition program for diabetes "
                "and weight management"
            ),
        }
    ) > _score_watch_item({"title": "Group appointment scheduling update"})
