from __future__ import annotations

from nutev.search.base import ProviderResult


def search_google_pse(query: str, *, limit: int = 10, context: dict | None = None) -> ProviderResult:
    return ProviderResult("google_pse", query, status="skipped", error="Google PSE is optional; configure GOOGLE_API_KEY and GOOGLE_CSE_ID")
