from __future__ import annotations
import requests
import time


def _pick_europepmc_url(item: dict) -> str:
    full_text = item.get("fullTextUrlList") or {}

    entries = []
    if isinstance(full_text, dict):
        entries = full_text.get("fullTextUrl", [])
    if isinstance(entries, dict):
        entries = [entries]

    for entry in entries:
        if isinstance(entry, dict) and entry.get("url"):
            return entry["url"]

    doi = item.get("doi")
    if doi:
        doi = str(doi).replace("doi:", "").strip()
        return f"https://doi.org/{doi}"

    pmid = item.get("pmid")
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    return ""


def search_europepmc(query: str, page_size: int = 18) -> list[dict]:
    import os
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last = None
    for attempt in range(1, 4):
        try:
            r = requests.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params={"query": query, "format": "json", "pageSize": page_size},
                timeout=45,
            )
            r.raise_for_status()
            results = r.json().get("resultList", {}).get("result", [])

            rows = []
            for it in results:
                rows.append(
                    {
                        "source": "europepmc",
                        "title": it.get("title"),
                        "doi": it.get("doi"),
                        "url": _pick_europepmc_url(it),
                    }
                )
            return rows
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    raise last