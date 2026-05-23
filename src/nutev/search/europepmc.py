from __future__ import annotations

import os
import re
import time
from typing import Any

import requests

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _clean_text(value: Any | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_pmcid(value: Any | None) -> str:
    raw = _clean_text(value)
    if not raw:
        return ""
    if raw.upper().startswith("PMC"):
        return raw.upper()
    if raw.isdigit():
        return f"PMC{raw}"
    return raw


def _extract_year(*values: Any | None) -> str:
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        match = _YEAR_RE.search(text)
        if match:
            return match.group(0)
    return ""


def _pick_europepmc_url(item: dict) -> str:
    pmcid = _normalize_pmcid(item.get("pmcid"))
    if pmcid:
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"

    full_text = item.get("fullTextUrlList") or {}
    entries = []
    if isinstance(full_text, dict):
        entries = full_text.get("fullTextUrl", [])
    if isinstance(entries, dict):
        entries = [entries]

    best_url = ""
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        url = _clean_text(entry.get("url"))
        if not url:
            continue
        if not best_url:
            best_url = url
        lower_url = url.lower()
        if lower_url.endswith(".pdf") or "/pdf" in lower_url:
            return url
        if "pmc.ncbi.nlm.nih.gov" in lower_url:
            return url

    if best_url:
        return best_url

    doi = _clean_text(item.get("doi")).removeprefix("doi:").strip()
    if doi:
        return f"https://doi.org/{doi}"

    pmid = _clean_text(item.get("pmid"))
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    return ""


def _normalize_result(item: dict) -> dict[str, str]:
    pmcid = _normalize_pmcid(item.get("pmcid"))
    publication_date = (
        _clean_text(item.get("firstPublicationDate"))
        or _clean_text(item.get("electronicPublicationDate"))
        or _clean_text(item.get("firstIndexDate"))
    )
    return {
        "source": "europepmc",
        "title": _clean_text(item.get("title")),
        "abstract": _clean_text(item.get("abstractText")),
        "summary": _clean_text(item.get("abstractText")),
        "doi": _clean_text(item.get("doi")),
        "pmid": _clean_text(item.get("pmid")),
        "pmcid": pmcid,
        "url": _pick_europepmc_url(item),
        "journal": _clean_text(item.get("journalTitle") or item.get("journal")),
        "year": _extract_year(
            item.get("pubYear"),
            item.get("firstPublicationDate"),
            item.get("electronicPublicationDate"),
            item.get("firstIndexDate"),
        ),
        "publication_date": publication_date,
        "article_type": _clean_text(item.get("pubType") or item.get("resultType")),
        "authors": _clean_text(item.get("authorString")),
        "metadata_status": "europepmc_search",
        "is_open_access": _clean_text(item.get("isOpenAccess")).lower(),
    }


def search_europepmc(query: str, page_size: int = 18) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last = None
    for attempt in range(1, 4):
        try:
            response = requests.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params={"query": query, "format": "json", "pageSize": page_size},
                timeout=45,
            )
            response.raise_for_status()
            results = response.json().get("resultList", {}).get("result", [])
            return [_normalize_result(item) for item in results]
        except Exception as exc:
            last = exc
            time.sleep(1.0 * attempt)
    raise last
