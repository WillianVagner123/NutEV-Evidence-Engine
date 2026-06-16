from __future__ import annotations
import logging
import os
import requests
import time

logger = logging.getLogger(__name__)


def _normalize_semantic_scholar(item: dict, query: str) -> dict:
    external_ids = item.get("externalIds") or {}
    if not isinstance(external_ids, dict):
        external_ids = {}

    doi = str(external_ids.get("DOI") or "").strip()
    if doi.lower().startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    doi = doi.lower()

    pmid = str(external_ids.get("PubMed") or "").strip()
    pmcid = str(external_ids.get("PubMedCentral") or "").strip()

    open_access = item.get("openAccessPdf") or {}
    if not isinstance(open_access, dict):
        open_access = {}
    oa_pdf_url = str(open_access.get("url") or "").strip()

    url = str(item.get("url") or "").strip() or oa_pdf_url

    abstract = str(item.get("abstract") or "")
    snippet = abstract[:300]

    authors_field = item.get("authors")
    if isinstance(authors_field, list):
        authors = "; ".join(
            str(a.get("name", "")).strip()
            for a in authors_field[:12]
            if isinstance(a, dict) and str(a.get("name", "")).strip()
        )
    else:
        authors = ""

    pub_types = item.get("publicationTypes")
    if isinstance(pub_types, list):
        article_type = "; ".join(str(p) for p in pub_types if p)
    else:
        article_type = ""

    year = str(item.get("year") or "").strip()
    is_open_access = "true" if oa_pdf_url else "false"

    return {
        "source": "semantic_scholar",
        "source_provider": "semantic_scholar",
        "title": str(item.get("title") or ""),
        "abstract": abstract,
        "snippet": snippet,
        "doi": doi,
        "pmid": pmid,
        "pmcid": pmcid,
        "url": url,
        "journal": str(item.get("venue") or ""),
        "year": year,
        "publication_date": year,
        "article_type": article_type,
        "authors": authors,
        "metadata_status": "semantic_scholar_search",
        "query": query,
        "provider_query": query,
        "oa_pdf_url": oa_pdf_url,
        "is_open_access": is_open_access,
    }


def search_semantic_scholar(query: str, *, limit: int = 20, context: dict | None = None) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []

    headers = {"User-Agent": "NutEV Research Pipeline/1.0"}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,abstract,year,venue,externalIds,openAccessPdf,authors,publicationTypes,url",
    }

    last = None
    for attempt in range(1, 4):
        try:
            r = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
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
            rows = [_normalize_semantic_scholar(it, query) for it in payload.get("data", [])]
            return rows
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    logger.warning("semantic_scholar search failed query=%s error=%s", query, last)
    return []
