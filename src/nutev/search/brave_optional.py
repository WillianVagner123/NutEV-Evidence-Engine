from __future__ import annotations

import os
import time
from typing import Any

import requests

from nutev.search.base import ProviderResult


def _row(item: dict[str, Any], query: str) -> dict[str, Any]:
    return {
        "source": "brave",
        "source_provider": "brave",
        "title": item.get("title") or "",
        "snippet": item.get("description") or "",
        "abstract": "",
        "summary": item.get("description") or "",
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "url": item.get("url") or "",
        "journal": "",
        "year": "",
        "publication_date": "",
        "article_type": "web",
        "authors": "",
        "metadata_status": "brave",
        "query": query,
        "provider_query": query,
    }


def search_brave(query: str, *, limit: int = 10, context: dict[str, Any] | None = None) -> ProviderResult:
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        return ProviderResult("brave", query, status="skipped", error="missing BRAVE_API_KEY")
    rows: list[dict[str, Any]] = []
    session = requests.Session()
    try:
        headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
        params = {"q": query, "count": min(limit, 20)}
        for attempt in range(1, 4):
            try:
                response = session.get("https://api.search.brave.com/res/v1/web/search", params=params, headers=headers, timeout=(10, 30))
                if response.status_code in {401, 403, 429, 500, 502, 503, 504}:
                    raise RuntimeError(f"Brave Search HTTP {response.status_code}")
                response.raise_for_status()
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise RuntimeError("invalid JSON from Brave Search") from exc
                items = (payload.get("web") or {}).get("results") or []
                if not isinstance(items, list) or not items:
                    return ProviderResult("brave", query, status="empty")
                rows = [_row(item, query) for item in items[:limit] if isinstance(item, dict)]
                return ProviderResult("brave", query, rows=rows, total_returned=len(rows), status="completed" if rows else "empty")
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(min(2**attempt, 8))
    except Exception as exc:
        return ProviderResult("brave", query, rows=rows, total_returned=len(rows), status="partial" if rows else "failed", error=str(exc))
    finally:
        session.close()
