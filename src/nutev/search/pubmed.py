from __future__ import annotations

import os
import re
import time
from typing import Any

import requests

DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.I)


def _clean_doi(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    raw = raw.replace("DOI:", " ").replace("doi:", " ")
    match = DOI_RE.search(raw)
    if not match:
        return None
    return match.group(1).rstrip(" .;,)")


def _pick_article_id(item: dict[str, Any], id_type: str) -> str | None:
    wanted = id_type.lower()
    for article_id in item.get("articleids", []) or []:
        if not isinstance(article_id, dict):
            continue
        if str(article_id.get("idtype", "")).lower() == wanted:
            value = article_id.get("value")
            if value:
                return str(value).strip()
    return None


def _extract_doi(item: dict[str, Any]) -> str | None:
    # PubMed's `elocationid` can be contaminated with strings such as
    # "pii: qdag137. doi: 10.1093/jsxmed/qdag137". Prefer structured
    # article IDs and always run DOI regex extraction before building a URL.
    return _clean_doi(_pick_article_id(item, "doi")) or _clean_doi(
        item.get("elocationid")
    )


def _extract_year(pubdate: str | None, epubdate: str | None = None) -> str:
    for value in [pubdate, epubdate]:
        if not value:
            continue
        match = re.search(r"\b(19|20)\d{2}\b", str(value))
        if match:
            return match.group(0)
    return ""


def _extract_authors(item: dict[str, Any], limit: int = 12) -> str:
    names: list[str] = []
    for author in item.get("authors", []) or []:
        if not isinstance(author, dict):
            continue
        name = author.get("name")
        if name:
            names.append(str(name))
    if len(names) > limit:
        return "; ".join(names[:limit]) + f"; +{len(names) - limit} more"
    return "; ".join(names)


def _pick_pubmed_url(pmid: str, doi: str | None, pmcid: str | None) -> str:
    # Prefer PMC when available because it is more likely to expose free full
    # text/PDF. DOI landing pages are useful fallback metadata, but they are the
    # most common source of 403/paywall noise in GitHub Actions.
    if pmcid:
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    if doi:
        return f"https://doi.org/{doi}"
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def search_pubmed(query: str, retmax: int = 18) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last = None
    for attempt in range(1, 4):
        try:
            esearch = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={"db": "pubmed", "retmode": "json", "term": query, "retmax": retmax},
                timeout=45,
            )
            esearch.raise_for_status()
            ids = esearch.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []

            summary = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)},
                timeout=45,
            )
            summary.raise_for_status()
            payload = summary.json().get("result", {})

            out = []
            for pmid in ids:
                item = payload.get(pmid, {})
                doi = _extract_doi(item)
                pmcid = _pick_article_id(item, "pmc")
                out.append(
                    {
                        "source": "pubmed",
                        "title": item.get("title"),
                        "doi": doi or "",
                        "pmid": pmid,
                        "pmcid": pmcid or "",
                        "url": _pick_pubmed_url(pmid, doi, pmcid),
                        "journal": item.get("fulljournalname") or item.get("source") or "",
                        "year": _extract_year(item.get("pubdate"), item.get("epubdate")),
                        "publication_date": item.get("pubdate") or item.get("epubdate") or "",
                        "article_type": "; ".join(item.get("pubtype", []) or []),
                        "authors": _extract_authors(item),
                        "metadata_status": "pubmed_esummary",
                    }
                )
            return out
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    raise last
