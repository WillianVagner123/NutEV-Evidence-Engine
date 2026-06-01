from __future__ import annotations

import os
import time
from typing import Any

import requests

from nutev.search.base import ProviderResult


def _row(item: dict[str, Any], query: str) -> dict[str, Any]:
    return {
        "source": "serpapi",
        "source_provider": "serpapi",
        "title": item.get("title") or "",
        "snippet": item.get("snippet") or "",
        "abstract": "",
        "summary": item.get("snippet") or "",
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "url": item.get("link") or "",
        "journal": "",
        "year": "",
        "publication_date": "",
        "article_type": "web",
        "authors": "",
        "metadata_status": "serpapi",
        "query": query,
        "provider_query": query,
    }


def search_serpapi(query: str, *, limit: int = 10, context: dict[str, Any] | None = None) -> ProviderResult:
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        return ProviderResult("serpapi", query, status="skipped", error="missing SERPAPI_API_KEY")
    rows: list[dict[str, Any]] = []
    session = requests.Session()
    try:
        params = {"engine": "google", "q": query, "api_key": api_key, "num": min(limit, 100)}
        for attempt in range(1, 4):
            try:
                response = session.get("https://serpapi.com/search.json", params=params, timeout=(10, 30))
                if response.status_code in {401, 403, 429, 500, 502, 503, 504}:
                    raise RuntimeError(f"SerpAPI HTTP {response.status_code}")
                response.raise_for_status()
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise RuntimeError("invalid JSON from SerpAPI") from exc
                if payload.get("error"):
                    raise RuntimeError(str(payload["error"]))
                items = payload.get("organic_results") or []
                if not isinstance(items, list) or not items:
                    return ProviderResult("serpapi", query, status="empty")
                rows = [_row(item, query) for item in items[:limit] if isinstance(item, dict)]
                return ProviderResult("serpapi", query, rows=rows, total_returned=len(rows), status="completed" if rows else "empty")
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(min(2**attempt, 8))
    except Exception as exc:
        return ProviderResult("serpapi", query, rows=rows, total_returned=len(rows), status="partial" if rows else "failed", error=str(exc))
    finally:
        session.close()
