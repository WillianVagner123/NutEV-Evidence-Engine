from __future__ import annotations

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

_SCIELO_PREFIX = "10.1590"


def _normalize_scielo(item: dict, query: str) -> dict:
    """Map a Crossref work (filtered to the SciELO DOI prefix) to the row schema.

    Pure function: no network access, no side effects.
    """
    titles = item.get("title")
    title = titles[0] if isinstance(titles, list) and titles else ""

    raw_doi = item.get("DOI") or ""
    doi = str(raw_doi).strip().lower()

    container = item.get("container-title")
    journal = container[0] if isinstance(container, list) and container else ""

    authors_raw = item.get("author")
    if isinstance(authors_raw, list):
        authors = "; ".join(
            " ".join(
                part
                for part in (
                    str(a.get("given", "")).strip(),
                    str(a.get("family", "")).strip(),
                )
                if part
            ).strip()
            for a in authors_raw[:12]
        )
    else:
        authors = ""

    date_parts = (
        (item.get("published-print") or item.get("published-online") or {}).get("date-parts")
        or [[]]
    )[0]
    year = str(date_parts[0]) if date_parts and date_parts[0] else ""
    publication_date = "-".join(str(x) for x in date_parts) if date_parts else ""

    if doi:
        url = f"https://doi.org/{doi}"
    else:
        url = item.get("URL", "") or ""

    abstract = item.get("abstract", "") or ""

    return {
        "source": "scielo",
        "source_provider": "scielo",
        "title": title,
        "abstract": abstract,
        "snippet": abstract,
        "doi": doi,
        "pmid": "",
        "pmcid": "",
        "url": url,
        "journal": journal,
        "year": year,
        "publication_date": publication_date,
        "article_type": item.get("type") or "",
        "authors": authors,
        "metadata_status": "scielo_search",
        "query": query,
        "provider_query": query,
        "oa_pdf_url": "",
        "is_open_access": "",
    }


def search_scielo(query: str, *, limit: int = 20, context: dict | None = None) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last = None
    for attempt in range(1, 4):
        try:
            response = requests.get(
                "https://api.crossref.org/works",
                params={
                    "query": query,
                    "rows": min(limit, 50),
                    "filter": f"prefix:{_SCIELO_PREFIX}",
                    **(
                        {"mailto": os.environ.get("CROSSREF_MAILTO")}
                        if os.environ.get("CROSSREF_MAILTO")
                        else {}
                    ),
                },
                timeout=(10, 45),
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            response.raise_for_status()
            items = response.json().get("message", {}).get("items", [])
            return [_normalize_scielo(it, query) for it in items]
        except Exception as exc:
            last = exc
            time.sleep(1.0 * attempt)
    logger.warning("scielo search failed query=%s error=%s", query, last)
    return []
