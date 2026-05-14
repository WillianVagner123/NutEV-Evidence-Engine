from __future__ import annotations
import requests


def _pick_europepmc_url(item: dict) -> str:
    full_text = item.get("fullTextUrlList") or {}

    if isinstance(full_text, dict):
        entries = full_text.get("fullTextUrl", [])
    else:
        entries = []

    if isinstance(entries, dict):
        entries = [entries]

    for entry in entries:
        if isinstance(entry, dict) and entry.get("url"):
            return entry["url"]

    if item.get("doi"):
        return f"https://doi.org/{item['doi']}"

    if item.get("pmid"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{item['pmid']}/"

    return ""


def search_europepmc(query: str, page_size: int = 5) -> list[dict]:
    r = requests.get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={"query": query, "format": "json", "pageSize": page_size},
        timeout=30,
    )
    r.raise_for_status()
    results = r.json().get("resultList", {}).get("result", [])

    rows = []
    for it in results:
        url = _pick_europepmc_url(it)
        rows.append(
            {
                "source": "europepmc",
                "title": it.get("title"),
                "doi": it.get("doi"),
                "url": url,
            }
        )
    return rows