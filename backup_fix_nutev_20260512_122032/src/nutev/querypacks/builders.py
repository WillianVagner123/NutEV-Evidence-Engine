from __future__ import annotations

from collections.abc import Iterable


def build_queries(keyword_taxonomy: dict, workstream: str) -> list[str]:
    ws = keyword_taxonomy.get("workstreams", {}).get(workstream, {})
    themes = ws.get("themes", [])
    base = ws.get("base_terms", [])
    queries: list[str] = []
    for term in base:
        for theme in themes:
            queries.append(f'"{term}" AND "{theme}"')
    return queries


def build_querypack(keyword_taxonomy: dict, workstreams: Iterable[str]) -> dict[str, list[str]]:
    return {ws: build_queries(keyword_taxonomy, ws) for ws in workstreams}
