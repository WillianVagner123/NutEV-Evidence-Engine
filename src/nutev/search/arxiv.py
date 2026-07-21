"""arXiv preprint-search connector (Atom API).

Adds preprint coverage via the public arXiv export API — no key required. The
API returns Atom XML, parsed with the stdlib ``xml.etree.ElementTree`` so no new
dependency is introduced. Follows the same connector contract as the other
providers: a reproducible single-page default, opt-in bounded pagination,
exponential backoff, and normalization to the shared row schema.
"""
from __future__ import annotations

import os
import time
from typing import Any
from xml.etree import ElementTree as ET

import requests

_ARXIV_URL = "http://export.arxiv.org/api/query"
_ATOM = "{http://www.w3.org/2005/Atom}"
_ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def _clean(value: Any) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def _text(node: ET.Element | None) -> str:
    return _clean(node.text) if node is not None else ""


def _entry_id(entry: ET.Element) -> str:
    """arXiv id like 2401.01234v2, derived from the entry <id> URL."""
    raw = _text(entry.find(f"{_ATOM}id"))
    return raw.rsplit("/abs/", 1)[-1] if "/abs/" in raw else raw


def _pick_url(entry: ET.Element) -> str:
    for link in entry.findall(f"{_ATOM}link"):
        if link.get("title") == "pdf" or link.get("type") == "application/pdf":
            return _clean(link.get("href"))
    return _text(entry.find(f"{_ATOM}id"))


def _normalize_entry(entry: ET.Element, query: str) -> dict:
    authors = "; ".join(
        _text(a.find(f"{_ATOM}name")) for a in entry.findall(f"{_ATOM}author") if _text(a.find(f"{_ATOM}name"))
    )
    doi = _text(entry.find(f"{_ARXIV_NS}doi"))
    published = _text(entry.find(f"{_ATOM}published"))
    abstract = _text(entry.find(f"{_ATOM}summary"))
    arxiv_id = _entry_id(entry)
    return {
        "source": "arxiv",
        "source_provider": "arxiv",
        "title": _text(entry.find(f"{_ATOM}title")),
        "abstract": abstract,
        "snippet": abstract,
        "doi": doi,
        "pmid": "",
        "pmcid": "",
        "url": _pick_url(entry),
        "journal": _text(entry.find(f"{_ARXIV_NS}journal_ref")),
        "year": published[:4],
        "publication_date": published[:10],
        "article_type": "preprint",
        "authors": authors,
        "registry_id": f"arXiv:{arxiv_id}" if arxiv_id else "",
        "metadata_status": "arxiv_search",
        "query": query,
        "provider_query": query,
    }


def _arxiv_get(query: str, start: int, max_results: int) -> list[ET.Element] | None:
    """GET one page with exponential backoff. Returns entry elements or None."""
    params = {"search_query": f"all:{query}", "start": start, "max_results": max_results}
    for attempt in range(1, 4):
        try:
            response = requests.get(
                _ARXIV_URL,
                params=params,
                timeout=45,
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            response.raise_for_status()
            root = ET.fromstring(response.content)
            return root.findall(f"{_ATOM}entry")
        except Exception:
            time.sleep(min(2 ** attempt, 8))
    return None


def _resolve_max_results(page_size: int, max_results: int | None) -> int:
    """Default (None) preserves single-page behaviour; opt into deeper recall with
    NUTEV_ARXIV_MAX_RESULTS so default runs stay reproducible."""
    if max_results is not None:
        return max(max_results, 0)
    env = os.environ.get("NUTEV_ARXIV_MAX_RESULTS", "")
    return int(env) if env.isdigit() and int(env) > 0 else page_size


def search_arxiv(query: str, page_size: int = 18, max_results: int | None = None) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    if os.environ.get("NUTEV_SKIP_ARXIV") == "1":
        return []

    # arXiv caps max_results per request at 100.
    page_size = max(1, min(page_size, 100))
    target = _resolve_max_results(page_size, max_results)

    # Single-page path — kept simple and reproducible.
    if target <= page_size:
        entries = _arxiv_get(query, 0, page_size)
        if not entries:
            return []
        return [_normalize_entry(e, query) for e in entries]

    # Paginated path — walk by `start` up to `target`, de-duplicating by id/title.
    collected: list[dict] = []
    seen: set[str] = set()
    start = 0
    while len(collected) < target:
        requested = min(page_size, target - len(collected))
        entries = _arxiv_get(query, start, requested)
        if not entries:
            break
        for entry in entries:
            row = _normalize_entry(entry, query)
            key = row["doi"] or row["registry_id"] or row["title"]
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            collected.append(row)
            if len(collected) >= target:
                break
        if len(entries) < requested:  # short page → no more results
            break
        start += requested
    return collected
