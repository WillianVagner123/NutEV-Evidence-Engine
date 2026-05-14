from __future__ import annotations
import requests


def _pick_openalex_url(item: dict) -> str:
    primary = item.get("primary_location") or {}
    best_oa = item.get("best_oa_location") or {}

    for candidate in [
        primary.get("pdf_url"),
        primary.get("landing_page_url"),
        best_oa.get("pdf_url"),
        best_oa.get("landing_page_url"),
        item.get("doi"),
        item.get("id"),
    ]:
        if candidate:
            return candidate

    return ""


def search_openalex(query: str, per_page: int = 10) -> list[dict]:
    r = requests.get(
        "https://api.openalex.org/works",
        params={"search": query, "per-page": per_page},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json().get("results", [])

    rows = []
    for it in data:
        url = _pick_openalex_url(it)
        rows.append(
            {
                "source": "openalex",
                "title": it.get("display_name"),
                "doi": it.get("doi"),
                "url": url,
            }
        )
    return rows