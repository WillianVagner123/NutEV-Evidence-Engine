"""CORE (core.ac.uk) open-access aggregator — optional provider.

CORE indexes tens of millions of open-access full texts and exposes a direct
``downloadUrl`` per work, so it both widens database coverage and increases how
many PDFs can be downloaded. It requires a free API key (CORE_API_KEY); without
one the provider reports ``skipped`` instead of failing.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

from nutev.search.base import ProviderResult, redact_secrets

logger = logging.getLogger(__name__)
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _clean_doi(doi: str | None) -> str:
    raw = str(doi or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "DOI:"):
        if raw.lower().startswith(prefix.lower()):
            raw = raw[len(prefix):]
    return raw.strip().strip("/").lower()


def _normalize_core(item: dict[str, Any], query: str) -> dict[str, Any]:
    download_url = str(item.get("downloadUrl") or "")
    authors = item.get("authors") or []
    author_names = "; ".join(
        str(a.get("name") or "").strip() for a in authors[:12] if isinstance(a, dict) and a.get("name")
    )
    abstract = str(item.get("abstract") or "")
    year = str(item.get("yearPublished") or "").strip()
    doi = _clean_doi(item.get("doi"))
    return {
        "source": "core",
        "source_provider": "core",
        "title": str(item.get("title") or ""),
        "abstract": abstract,
        "snippet": abstract[:300],
        "doi": doi,
        "pmid": "",
        "pmcid": "",
        "url": download_url or (f"https://doi.org/{doi}" if doi else ""),
        "journal": str(item.get("publisher") or ""),
        "year": year if year.isdigit() else "",
        "publication_date": str(item.get("publishedDate") or ""),
        "article_type": str(item.get("documentType") or ""),
        "authors": author_names,
        "metadata_status": "core_search",
        "query": query,
        "provider_query": query,
        "oa_pdf_url": download_url,
        "is_open_access": "true",
    }


def search_core(query: str, *, limit: int = 20, context: dict[str, Any] | None = None) -> ProviderResult | list[dict[str, Any]]:
    api_key = os.environ.get("CORE_API_KEY")
    if not api_key:
        return ProviderResult("core", query, status="skipped", error="missing CORE_API_KEY")
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = requests.post(
                "https://api.core.ac.uk/v3/search/works",
                headers={"Authorization": f"Bearer {api_key}", "User-Agent": "NutEV Research Pipeline/1.0"},
                json={"q": query, "limit": min(limit, 100)},
                timeout=(10, 30),
            )
            if response.status_code in RETRY_STATUSES:
                raise RuntimeError(f"CORE HTTP {response.status_code}")
            response.raise_for_status()
            results = response.json().get("results", []) or []
            return [_normalize_core(item, query) for item in results if isinstance(item, dict)]
        except Exception as exc:
            last = exc
            if attempt == 3:
                break
            time.sleep(min(2 ** attempt, 8))
    return ProviderResult("core", query, status="failed", error=redact_secrets(last))
