from __future__ import annotations
import requests
import time


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
    last = None
    for attempt in range(1, 4):
        try:
            r = requests.get(
                "https://api.crossref.org/works",
                params={"query": query, "rows": rows},
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
                        "title": titles[0] if titles else "",
                        "doi": it.get("DOI"),
                        "url": _pick_crossref_url(it),
                    }
                )
            return out
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    raise last