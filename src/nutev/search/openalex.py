from __future__ import annotations

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


def _reconstruct_abstract(inverted_index: object) -> str:
    """Rebuild an OpenAlex abstract from its inverted index.

    The index maps each word to the list of positions where it occurs; the
    abstract must be reassembled in positional order. Joining ``.keys()`` (the
    previous behaviour) scrambles word order and drops repeated words.
    """
    if not isinstance(inverted_index, dict) or not inverted_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted_index.items():
        if isinstance(idxs, list):
            positions.extend((pos, word) for pos in idxs if isinstance(pos, int))
    positions.sort(key=lambda pair: pair[0])
    return " ".join(word for _, word in positions)


def _pick_openalex_url(item: dict) -> str:
    primary = item.get("primary_location") or {}
    best_oa = item.get("best_oa_location") or {}

    for candidate in [
        primary.get("pdf_url"),
        primary.get("landing_page_url"),
        best_oa.get("pdf_url"),
        best_oa.get("landing_page_url"),
        item.get("doi"),
        item.get("id"),
    ]:
        if candidate:
            return candidate

    return ""


def search_openalex(query: str, per_page: int = 12) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []

    last: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = requests.get(
                "https://api.openalex.org/works",
                params={"search": query, "per-page": per_page, **({"mailto": os.environ.get("OPENALEX_MAILTO")} if os.environ.get("OPENALEX_MAILTO") else {})},
                timeout=(10, 25),
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("results", [])

            rows = []
            for item in data:
                rows.append(
                    {
                        "source": "openalex",
                        "source_provider": "openalex",
                        "title": item.get("display_name"),
                        "abstract": _reconstruct_abstract(item.get("abstract_inverted_index")),
                        "snippet": "",
                        "doi": item.get("doi"),
                        "url": _pick_openalex_url(item),
                        "journal": ((item.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                        "year": item.get("publication_year") or "",
                        "publication_date": item.get("publication_date") or "",
                        "article_type": item.get("type") or "",
                        "authors": "; ".join([str((a.get("author") or {}).get("display_name") or "") for a in item.get("authorships", [])[:12]]) if isinstance(item.get("authorships"), list) else "",
                        "metadata_status": "openalex_search",
                        "query": query,
                        "provider_query": query,
                    }
                )
            return rows

        except Exception as exc:
            last = exc
            time.sleep(1.0 * attempt)

    logger.warning("openalex search failed query=%s error=%s", query, last)
    return []
