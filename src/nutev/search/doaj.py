from __future__ import annotations
import logging
import os
import time
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


def _normalize_doaj(item: dict, query: str) -> dict:
    bibjson = item.get("bibjson") or {}
    if not isinstance(bibjson, dict):
        bibjson = {}

    title = str(bibjson.get("title") or "")
    abstract = str(bibjson.get("abstract") or "")
    snippet = abstract[:300]

    year = str(bibjson.get("year") or "").strip()

    journal = bibjson.get("journal") or {}
    if isinstance(journal, dict):
        journal_title = str(journal.get("title") or "")
    else:
        journal_title = ""

    authors_field = bibjson.get("author")
    if isinstance(authors_field, list):
        authors = "; ".join(
            str(a.get("name", "")).strip()
            for a in authors_field[:12]
            if isinstance(a, dict) and str(a.get("name", "")).strip()
        )
    else:
        authors = ""

    doi = ""
    identifiers = bibjson.get("identifier")
    if isinstance(identifiers, list):
        for ident in identifiers:
            if not isinstance(ident, dict):
                continue
            if str(ident.get("type") or "").lower() == "doi":
                doi = str(ident.get("id") or "").strip()
                break
    if doi.lower().startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    doi = doi.lower()

    url = ""
    oa_pdf_url = ""
    links = bibjson.get("link")
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            link_url = str(link.get("url") or "").strip()
            if not link_url:
                continue
            if not url:
                url = link_url
            link_type = str(link.get("type") or "").lower()
            if not oa_pdf_url and ("fulltext" in link_type or "pdf" in link_type):
                oa_pdf_url = link_url

    return {
        "source": "doaj",
        "source_provider": "doaj",
        "title": title,
        "abstract": abstract,
        "snippet": snippet,
        "doi": doi,
        "pmid": "",
        "pmcid": "",
        "url": url,
        "journal": journal_title,
        "year": year,
        "publication_date": year,
        "article_type": "",
        "authors": authors,
        "metadata_status": "doaj_search",
        "query": query,
        "provider_query": query,
        "oa_pdf_url": oa_pdf_url,
        "is_open_access": "true",
    }


def search_doaj(query: str, *, limit: int = 20, context: dict | None = None) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []

    headers = {"User-Agent": "NutEV Research Pipeline/1.0"}
    params = {"pageSize": min(limit, 100)}
    url = f"https://doaj.org/api/search/articles/{quote(query)}"

    last = None
    for attempt in range(1, 4):
        try:
            r = requests.get(
                url,
                params=params,
                timeout=(10, 30),
                headers=headers,
            )
            if r.status_code == 429 or r.status_code >= 500:
                last = f"HTTP {r.status_code}"
                time.sleep(1.0 * attempt)
                continue
            r.raise_for_status()
            payload = r.json()
            rows = [_normalize_doaj(it, query) for it in payload.get("results", [])]
            return rows
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    logger.warning("doaj search failed query=%s error=%s", query, last)
    return []
