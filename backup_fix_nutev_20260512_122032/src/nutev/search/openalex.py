from __future__ import annotations
import requests


def search_openalex(query: str, per_page: int = 5) -> list[dict]:
    r = requests.get("https://api.openalex.org/works", params={"search": query, "per-page": per_page}, timeout=30)
    r.raise_for_status()
    data = r.json().get("results", [])
    return [{"source": "openalex", "title": it.get("display_name"), "doi": it.get("doi"), "url": it.get("id")} for it in data]
