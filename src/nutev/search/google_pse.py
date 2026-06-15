from __future__ import annotations

import os
import time
from typing import Any

import requests

from nutev.search.base import ProviderResult, redact_secrets

RETRY_STATUSES = {429, 500, 502, 503, 504}


def _safe_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("invalid JSON from Google PSE") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("invalid Google PSE payload")
    return payload


def _row(item: dict[str, Any], query: str) -> dict[str, Any]:
    return {
        "source": "google_pse",
        "source_provider": "google_pse",
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
        "metadata_status": "google_pse",
        "query": query,
        "provider_query": query,
    }


def search_google_pse(query: str, *, limit: int = 10, context: dict[str, Any] | None = None) -> ProviderResult:
    api_key = os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        return ProviderResult("google_pse", query, status="skipped", error="missing GOOGLE_API_KEY/GOOGLE_CSE_ID")
    rows: list[dict[str, Any]] = []
    total: int | None = None
    start = 1
    session = requests.Session()
    try:
        while len(rows) < limit and start <= 91:
            params = {"key": api_key, "cx": cse_id, "q": query, "num": min(10, limit - len(rows)), "start": start}
            last_error: Exception | None = None
            for attempt in range(1, 4):
                try:
                    response = session.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=(10, 30))
                    if response.status_code in {401, 403}:
                        payload = _safe_json(response)
                        raise RuntimeError(payload.get("error", {}).get("message") or f"Google PSE HTTP {response.status_code}")
                    if response.status_code in RETRY_STATUSES:
                        raise RuntimeError(f"Google PSE HTTP {response.status_code}")
                    response.raise_for_status()
                    payload = _safe_json(response)
                    total = int((payload.get("searchInformation") or {}).get("totalResults") or 0)
                    items = payload.get("items") or []
                    if not isinstance(items, list) or not items:
                        return ProviderResult("google_pse", query, rows=rows, total_found=total, total_returned=len(rows), status="completed" if rows else "empty")
                    rows.extend(_row(item, query) for item in items if isinstance(item, dict))
                    break
                except Exception as exc:
                    last_error = exc
                    if "quota" in str(exc).lower() or "limit" in str(exc).lower() or attempt == 3:
                        raise
                    time.sleep(min(2**attempt, 8))
            if last_error and not rows:
                raise last_error
            start += 10
            time.sleep(0.2)
        return ProviderResult("google_pse", query, rows=rows[:limit], total_found=total, total_returned=len(rows[:limit]), status="completed" if rows else "empty")
    except Exception as exc:
        return ProviderResult("google_pse", query, rows=rows[:limit], total_found=total, total_returned=len(rows[:limit]), status="partial" if rows else "failed", error=redact_secrets(exc))
    finally:
        session.close()
