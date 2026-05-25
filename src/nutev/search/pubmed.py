from __future__ import annotations

import os
import re
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.I)
DOI_URL_RE = re.compile(r"https?://(?:dx\.)?doi\.org/", re.I)
PMCID_RE = re.compile(r"\bPMC\s*([0-9]+)\b", re.I)
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedUnavailable(RuntimeError):
    """Raised only after all PubMed request fallbacks fail."""


def _clean_doi(value: Any | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    raw = DOI_URL_RE.sub(" ", raw)
    raw = raw.replace("doi.org/", " ")
    raw = raw.replace("DOI:", " ").replace("doi:", " ")
    match = DOI_RE.search(raw)
    if not match:
        return None
    return match.group(1).rstrip(" .;,)]}")


def _clean_pmcid(value: Any | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    match = PMCID_RE.search(raw)
    if match:
        return f"PMC{match.group(1)}"
    if raw.isdigit():
        return f"PMC{raw}"
    return raw


def _pick_article_id(item: dict[str, Any], *id_types: str) -> str | None:
    wanted = {id_type.lower() for id_type in id_types}
    for article_id in item.get("articleids", []) or []:
        if not isinstance(article_id, dict):
            continue
        if str(article_id.get("idtype", "")).lower() in wanted:
            value = article_id.get("value")
            if value:
                return str(value).strip()
    return None


def _extract_doi(item: dict[str, Any]) -> str | None:
    return _clean_doi(_pick_article_id(item, "doi")) or _clean_doi(item.get("elocationid"))


def _extract_pmcid(item: dict[str, Any]) -> str | None:
    return _clean_pmcid(_pick_article_id(item, "pmc", "pmcid"))


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
    if pmcid:
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    if doi:
        return f"https://doi.org/{doi}"
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def _ncbi_params(params: dict[str, Any]) -> dict[str, Any]:
    out = dict(params)
    out["tool"] = os.environ.get("NCBI_TOOL", "nutev_pipeline")
    email = os.environ.get("NCBI_EMAIL") or os.environ.get("ENTREZ_EMAIL")
    api_key = os.environ.get("NCBI_API_KEY")
    if email:
        out["email"] = email
    if api_key:
        out["api_key"] = api_key
    return out


def _session() -> requests.Session:
    retries = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=8, pool_maxsize=8)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": "NutEV/0.1 (+https://github.com/WillianVagner123/NUT-MEV_NEW)",
            "Accept": "application/json,text/plain,*/*",
            "Connection": "close",
        }
    )
    return session


def _request_json(endpoint: str, params: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
    url = f"{EUTILS_BASE}/{endpoint}"
    params = _ncbi_params(params)
    last_error: Exception | None = None

    for attempt in range(1, 5):
        with _session() as session:
            for method in ("get", "post"):
                try:
                    if method == "get":
                        response = session.get(url, params=params, timeout=timeout)
                    else:
                        response = session.post(url, data=params, timeout=timeout)
                    response.raise_for_status()
                    return response.json()
                except Exception as exc:
                    last_error = exc
        time.sleep(min(2 * attempt, 8))

    raise PubMedUnavailable(f"PubMed E-utilities request failed after retries: {last_error}")


def search_pubmed(query: str, retmax: int = 18) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    if os.environ.get("NUTEV_SKIP_PUBMED") == "1":
        return []

    esearch_payload = _request_json(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "retmode": "json",
            "term": query,
            "retmax": retmax,
        },
    )
    ids = esearch_payload.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    summary_payload = _request_json(
        "esummary.fcgi",
        {
            "db": "pubmed",
            "retmode": "json",
            "id": ",".join(ids),
        },
    )
    payload = summary_payload.get("result", {})

    out = []
    for pmid in ids:
        item = payload.get(pmid, {})
        doi = _extract_doi(item)
        pmcid = _extract_pmcid(item)
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
