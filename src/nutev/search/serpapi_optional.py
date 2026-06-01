from __future__ import annotations

from nutev.search.base import ProviderResult


def search_serpapi(query: str, *, limit: int = 10, context: dict | None = None) -> ProviderResult:
    return ProviderResult("serpapi", query, status="skipped", error="SerpAPI is optional; configure SERPAPI_API_KEY")
