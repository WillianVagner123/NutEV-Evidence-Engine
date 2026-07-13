from __future__ import annotations

import os
import time

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


def search_openalex(query: str, per_page: int = 12) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []

    for attempt in range(1, 4):
        try:
            response = requests.get(
                "https://api.openalex.org/works",
                params={"search": query, "per-page": per_page, **({"mailto": os.environ.get("OPENALEX_MAILTO")} if os.environ.get("OPENALEX_MAILTO") else {})},
                timeout=(10, 25),
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("results", [])

            rows = []
            for item in data:
                rows.append(
                    {
                        "source": "openalex",
                        "source_provider": "openalex",
                        "title": item.get("display_name"),
                        "abstract": " ".join((item.get("abstract_inverted_index") or {}).keys()) if isinstance(item.get("abstract_inverted_index"), dict) else "",
                        "snippet": "",
                        "doi": item.get("doi"),
                        "url": _pick_openalex_url(item),
                        "pmcid": str((item.get("ids") or {}).get("pmcid") or "").rsplit("/", 1)[-1],
                        "is_open_access": str(bool((item.get("open_access") or {}).get("is_oa"))).lower(),
                        "oa_url": (item.get("open_access") or {}).get("oa_url")
                        or (item.get("best_oa_location") or {}).get("pdf_url")
                        or (item.get("best_oa_location") or {}).get("landing_page_url")
                        or "",
                        "journal": ((item.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                        "year": item.get("publication_year") or "",
                        "publication_date": item.get("publication_date") or "",
                        "article_type": item.get("type") or "",
                        "authors": "; ".join([str((a.get("author") or {}).get("display_name") or "") for a in item.get("authorships", [])[:12]]) if isinstance(item.get("authorships"), list) else "",
                        "metadata_status": "openalex_search",
                        "query": query,
                        "provider_query": query,
                    }
                )
            return rows

        except Exception:
            time.sleep(1.0 * attempt)

    return []
