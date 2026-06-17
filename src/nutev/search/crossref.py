from __future__ import annotations
import logging
import os
import requests
import time

logger = logging.getLogger(__name__)


def _pick_crossref_url(item: dict) -> str:
    for link in item.get("link", []) or []:
        if isinstance(link, dict):
            href = link.get("URL") or link.get("url")
            ctype = (link.get("content-type") or "").lower()
            if href and ("pdf" in ctype or href.lower().endswith(".pdf")):
                return href

    doi = item.get("DOI")
    if doi:
        return f"https://doi.org/{doi}"

    resource = item.get("resource") or {}
    primary = resource.get("primary") or {}
    if primary.get("URL"):
        return primary["URL"]

    return item.get("URL") or ""


def _crossref_affiliations(item: dict) -> list[str]:
    """Author affiliation names from Crossref ``author[].affiliation[].name``.

    Crossref usually omits affiliations, so this is commonly ``[]``. Names are
    de-duplicated preserving order.
    """
    out: list[str] = []
    authors = item.get("author")
    if not isinstance(authors, list):
        return out
    for author in authors:
        if not isinstance(author, dict):
            continue
        for aff in author.get("affiliation") or []:
            if isinstance(aff, dict):
                name = str(aff.get("name") or "").strip()
                if name and name not in out:
                    out.append(name)
    return out


def _crossref_date_parts(it: dict) -> list:
    """Numeric date components for a Crossref work, robust to empty ``[[]]`` blocks."""
    block = it.get("published-print") or it.get("published-online") or it.get("issued") or {}
    parts = block.get("date-parts") if isinstance(block, dict) else None
    if isinstance(parts, list) and parts and isinstance(parts[0], list):
        return [p for p in parts[0] if p not in (None, "")]
    return []


def _normalize_crossref(it: dict, query: str) -> dict:
    """Map a Crossref work to the row schema. Pure: no network, no side effects."""
    titles = it.get("title") or [""]
    issn_list = it.get("ISSN")
    issn = issn_list[0] if isinstance(issn_list, list) and issn_list else ""
    date_parts = _crossref_date_parts(it)
    return {
        "source": "crossref",
        "source_provider": "crossref",
        "title": titles[0] if titles else "",
        "abstract": it.get("abstract") or "",
        "snippet": it.get("abstract") or "",
        "doi": it.get("DOI"),
        "pmid": "",
        "pmcid": "",
        "url": _pick_crossref_url(it),
        "journal": (it.get("container-title") or [""])[0] if isinstance(it.get("container-title"), list) else "",
        "year": str(date_parts[0]) if date_parts else "",
        "publication_date": "-".join(str(x) for x in date_parts),
        "article_type": it.get("type") or "",
        "authors": "; ".join([" ".join([str(a.get("given", "")), str(a.get("family", ""))]).strip() for a in it.get("author", [])[:12]]) if isinstance(it.get("author"), list) else "",
        "publisher": it.get("publisher") or "",
        "issn": issn or "",
        "language": it.get("language") or "",
        "affiliations": _crossref_affiliations(it),
        "metadata_status": "crossref_search",
        "query": query,
        "provider_query": query,
    }


def search_crossref(query: str, rows: int = 18) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last = None
    for attempt in range(1, 4):
        try:
            r = requests.get(
                "https://api.crossref.org/works",
                params={"query": query, "rows": rows, **({"mailto": os.environ.get("CROSSREF_MAILTO")} if os.environ.get("CROSSREF_MAILTO") else {})},
                timeout=(10, 45),
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            r.raise_for_status()
            items = r.json().get("message", {}).get("items", [])
            return [_normalize_crossref(it, query) for it in items]
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    logger.warning("crossref search failed query=%s error=%s", query, last)
    return []