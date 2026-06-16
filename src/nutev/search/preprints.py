from __future__ import annotations

import logging
import os
import re
import time

import requests

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _clean_text(value: object | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _extract_year(*values: object | None) -> str:
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        match = _YEAR_RE.search(text)
        if match:
            return match.group(0)
    return ""


def _normalize_preprint(item: dict, query: str) -> dict:
    """Map a Europe PMC preprint result to the row schema.

    Pure function: no network access, no side effects.
    """
    doi = _clean_text(item.get("doi")).removeprefix("doi:").strip()
    url = f"https://doi.org/{doi}" if doi else ""

    journal = _clean_text(item.get("journalTitle") or item.get("bookOrReportDetails"))

    publication_date = _clean_text(item.get("firstPublicationDate"))

    return {
        "source": "preprints",
        "source_provider": "preprints",
        "title": _clean_text(item.get("title")),
        "abstract": _clean_text(item.get("abstractText")),
        "snippet": _clean_text(item.get("abstractText")),
        "doi": doi,
        "pmid": _clean_text(item.get("pmid")),
        "pmcid": _clean_text(item.get("pmcid")),
        "url": url,
        "journal": journal,
        "year": _extract_year(item.get("pubYear"), item.get("firstPublicationDate")),
        "publication_date": publication_date,
        "article_type": "preprint",
        "authors": _clean_text(item.get("authorString")),
        "metadata_status": "preprints_search",
        "query": query,
        "provider_query": query,
        "oa_pdf_url": "",
        "is_open_access": "true",
    }


def search_preprints(query: str, *, limit: int = 20, context: dict | None = None) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last = None
    for attempt in range(1, 4):
        try:
            response = requests.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params={
                    "query": f"({query}) AND SRC:PPR",
                    "format": "json",
                    "pageSize": min(limit, 100),
                },
                timeout=(10, 45),
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            response.raise_for_status()
            results = response.json().get("resultList", {}).get("result", [])
            return [_normalize_preprint(it, query) for it in results]
        except Exception as exc:
            last = exc
            time.sleep(1.0 * attempt)
    logger.warning("preprints search failed query=%s error=%s", query, last)
    return []
