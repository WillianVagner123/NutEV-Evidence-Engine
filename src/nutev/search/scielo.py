"""SciELO (Scientific Electronic Library Online) search connector.

SciELO has no clean public free-text JSON search API, and scraping its search
site is out of scope (the audit's no-scraping policy). SciELO-published articles
*are* registered with Crossref, so this connector retrieves SciELO content
reliably through the **stable, documented Crossref API**, restricted to SciELO's
DOI prefix ``10.1590`` (SciELO Brazil, the large majority of the corpus). This is
honest about coverage (prefix-scoped, not every regional collection) and avoids
guessing at an undocumented endpoint.

Rows reuse the proven Crossref normalization and are re-tagged as ``scielo``.
Same connector contract as the others: timeout + exponential backoff, a
reproducible single-page default, opt-in bounded pagination with dedup.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

from nutev.search.crossref import _normalize_crossref_item

_CROSSREF_URL = "https://api.crossref.org/works"
# SciELO Brazil DOI prefix. Content registered under this prefix is SciELO's.
SCIELO_DOI_PREFIX = "10.1590"


def _retag(row: dict, query: str) -> dict:
    row = dict(row)
    row["source"] = "scielo"
    row["source_provider"] = "scielo"
    row["metadata_status"] = "scielo_search"
    row["query"] = query
    row["provider_query"] = query
    return row


def _mailto() -> dict:
    mailto = os.environ.get("CROSSREF_MAILTO")
    return {"mailto": mailto} if mailto else {}


def _scielo_get(query: str, rows: int, offset: int) -> dict | None:
    """Query Crossref restricted to the SciELO prefix, with exponential backoff."""
    params: dict[str, Any] = {
        "query": query,
        "rows": rows,
        "offset": offset,
        "filter": f"prefix:{SCIELO_DOI_PREFIX}",
        **_mailto(),
    }
    for attempt in range(1, 4):
        try:
            r = requests.get(
                _CROSSREF_URL,
                params=params,
                timeout=45,
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(min(2 ** attempt, 8))
    return None


def _resolve_max_results(default: int, max_results: int | None) -> int:
    """Default (None) preserves single-page behaviour; opt in with
    NUTEV_SCIELO_MAX_RESULTS so default runs stay reproducible."""
    if max_results is not None:
        return max(max_results, 0)
    env = os.environ.get("NUTEV_SCIELO_MAX_RESULTS", "")
    return int(env) if env.isdigit() and int(env) > 0 else default


def search_scielo(query: str, rows: int = 18, max_results: int | None = None) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    if os.environ.get("NUTEV_SKIP_SCIELO") == "1":
        return []

    target = _resolve_max_results(rows, max_results)

    # Single-page path — identical shape to the Crossref connector (no offset).
    if target <= rows:
        data = _scielo_get(query, rows, 0)
        if not data:
            return []
        items = data.get("message", {}).get("items", []) or []
        return [_retag(_normalize_crossref_item(it, query), query) for it in items]

    # Paginated path — offset walk up to `target`, de-duplicating by DOI/title.
    collected: list[dict] = []
    seen: set[str] = set()
    offset = 0
    while len(collected) < target:
        page = min(rows, target - len(collected))
        data = _scielo_get(query, page, offset)
        if not data:
            break
        items = data.get("message", {}).get("items", []) or []
        if not items:
            break
        for it in items:
            row = _retag(_normalize_crossref_item(it, query), query)
            key = row.get("doi") or row.get("title")
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            collected.append(row)
            if len(collected) >= target:
                break
        if len(items) < page:
            break
        offset += page
    return collected
