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
                params={"search": query, "per-page": per_page},
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
                        "title": item.get("display_name"),
                        "doi": item.get("doi"),
                        "url": _pick_openalex_url(item),
                    }
                )
            return rows

        except Exception:
            time.sleep(1.0 * attempt)

    return []
