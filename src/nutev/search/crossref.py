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


def search_crossref(query: str, rows: int = 18) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last = None
    for attempt in range(1, 4):
        try:
            r = requests.get(
                "https://api.crossref.org/works",
                params={"query": query, "rows": rows, **({"mailto": os.environ.get("CROSSREF_MAILTO")} if os.environ.get("CROSSREF_MAILTO") else {})},
                timeout=45,
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            r.raise_for_status()
            items = r.json().get("message", {}).get("items", [])

            out = []
            for it in items:
                titles = it.get("title") or [""]
                out.append(
                    {
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
                        "year": str(((it.get("published-print") or it.get("published-online") or {}).get("date-parts") or [[""]])[0][0] or ""),
                        "publication_date": "-".join(str(x) for x in (((it.get("published-print") or it.get("published-online") or {}).get("date-parts") or [[]])[0])),
                        "article_type": it.get("type") or "",
                        "authors": "; ".join([" ".join([str(a.get("given", "")), str(a.get("family", ""))]).strip() for a in it.get("author", [])[:12]]) if isinstance(it.get("author"), list) else "",
                        "metadata_status": "crossref_search",
                        "query": query,
                        "provider_query": query,
                    }
                )
            return out
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    logger.warning("crossref search failed query=%s error=%s", query, last)
    return []