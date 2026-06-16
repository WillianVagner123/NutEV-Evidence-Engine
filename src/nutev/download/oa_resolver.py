"""Open-access full-text resolution to maximize how many files are downloaded.

Given a normalized record (with doi/pmid/pmcid and, for some providers, an
``oa_pdf_url``), this finds a legal open-access PDF to download, in order of
confidence:

1. an ``oa_pdf_url`` already supplied by the provider (Semantic Scholar, DOAJ,
   OpenAlex best_oa_location, ...);
2. Unpaywall (``best_oa_location.url_for_pdf``) keyed by DOI;
3. the PMC open-access PDF render for a PMCID.

All calls are best-effort and fail soft (return ``None``) so they never abort a
download run, and they honor ``NUTEV_DISABLE_NETWORK``.
"""

from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = (10, 30)
_HEADERS = {"User-Agent": "NutEV Research Pipeline/1.0 (mailto:%s)"}


def _network_disabled() -> bool:
    return os.environ.get("NUTEV_DISABLE_NETWORK") == "1"


def _contact_email() -> str:
    for key in ("UNPAYWALL_EMAIL", "NCBI_EMAIL", "ENTREZ_EMAIL", "CROSSREF_MAILTO", "OPENALEX_MAILTO"):
        value = os.environ.get(key)
        if value:
            return value
    return ""


def _clean_doi(doi: str | None) -> str:
    raw = str(doi or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "DOI:"):
        if raw.lower().startswith(prefix.lower()):
            raw = raw[len(prefix):]
    return raw.strip().strip("/")


def unpaywall_pdf_url(doi: str | None, email: str | None = None) -> str | None:
    """Return the best open-access PDF URL for a DOI via Unpaywall, or None."""
    clean = _clean_doi(doi)
    contact = email or _contact_email()
    if not clean or not contact or _network_disabled():
        return None
    try:
        response = requests.get(
            f"https://api.unpaywall.org/v2/{clean}",
            params={"email": contact},
            timeout=_TIMEOUT,
            headers={"User-Agent": "NutEV Research Pipeline/1.0"},
        )
        if response.status_code != 200:
            return None
        payload = response.json()
    except Exception as exc:
        logger.debug("unpaywall lookup failed doi=%s error=%s", clean, exc)
        return None

    best = payload.get("best_oa_location") or {}
    url = best.get("url_for_pdf") or best.get("url")
    if url:
        return str(url)
    for location in payload.get("oa_locations") or []:
        candidate = location.get("url_for_pdf") or location.get("url")
        if candidate:
            return str(candidate)
    return None


def _clean_pmcid(pmcid: str | None) -> str:
    raw = str(pmcid or "").strip().upper()
    return raw[3:] if raw.startswith("PMC") else raw


def pmc_pdf_url(pmcid: str | None) -> str | None:
    """Return the PMC open-access PDF URL for a PMCID, or None."""
    num = _clean_pmcid(pmcid)
    if not num or not num.isdigit():
        return None
    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{num}/pdf/"


def resolve_oa_pdf(record: dict, email: str | None = None) -> str | None:
    """Best open-access PDF URL for a record, or None when none is found."""
    if not isinstance(record, dict):
        return None

    supplied = str(record.get("oa_pdf_url") or "").strip()
    if supplied:
        return supplied

    if _network_disabled():
        return None

    from_unpaywall = unpaywall_pdf_url(record.get("doi"), email)
    if from_unpaywall:
        return from_unpaywall

    return pmc_pdf_url(record.get("pmcid"))
