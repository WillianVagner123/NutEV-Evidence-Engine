"""P2.2 — Full-text resolver for clinical guidelines (busca2a/busca2b).

Indexed-database search is used only for *discovery* (metadata). This module
resolves an open-access full-text location for a record, in this fallback order:

    (a) an existing PMCID              -> PMC free full text
    (b) DOI  -> Unpaywall              -> best_oa_location.url_for_pdf
    (c) PMID -> E-utilities elink      -> PMCID -> PMC free full text
    (d) none -> fulltext_status="paywall" (queue for institutional access)

It NEVER fabricates text and never bypasses a paywall — it only finds a
legitimately open location. The actual download reuses the existing downloader;
this module returns the resolved URL + provenance. The HTTP session is injected
(mockable, rate-limitable) and results are cached. Secrets (the Unpaywall email)
come from the caller / environment.
"""
from __future__ import annotations

from typing import Any

_PMC_URL = "https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
_UNPAYWALL = "https://api.unpaywall.org/v2/{doi}?email={email}"
_ELINK = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    "?dbfrom=pubmed&db=pmc&id={pmid}&retmode=json"
)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _norm_pmcid(pmcid: str) -> str:
    pmcid = pmcid.strip().upper()
    if pmcid and not pmcid.startswith("PMC"):
        pmcid = f"PMC{pmcid}"
    return pmcid


def _unpaywall_pdf(doi: str, email: str, session: Any, timeout: float) -> str:
    try:
        resp = session.get(_UNPAYWALL.format(doi=doi.lower(), email=email), timeout=timeout)
        if getattr(resp, "status_code", 0) != 200:
            return ""
        data = resp.json()
        if not data.get("is_oa"):
            return ""
        loc = data.get("best_oa_location") or {}
        return _clean(loc.get("url_for_pdf") or loc.get("url"))
    except Exception:
        return ""


def _pmcid_from_pmid(pmid: str, session: Any, timeout: float) -> str:
    """Resolve a PMID to a PMCID via E-utilities elink (pubmed -> pmc)."""
    try:
        resp = session.get(_ELINK.format(pmid=pmid), timeout=timeout)
        if getattr(resp, "status_code", 0) != 200:
            return ""
        data = resp.json()
        for linkset in data.get("linksets", []):
            for db in linkset.get("linksetdbs", []):
                if db.get("dbto") == "pmc":
                    for link in db.get("links", []):
                        return _norm_pmcid(str(link))
    except Exception:
        return ""
    return ""


def resolve_fulltext(
    record: dict,
    *,
    email: str | None = None,
    session: Any | None = None,
    cache: dict[str, dict] | None = None,
    timeout: float = 20.0,
) -> dict:
    """Return the best open-access full-text location for a record.

    Result keys: ``fulltext_status`` (``fulltext_oa`` | ``paywall`` |
    ``needs_network``), ``retrieval_method`` (``existing_pmcid`` | ``unpaywall``
    | ``pmc_elink`` | ``none``), ``fulltext_url`` and ``pmcid``. No download is
    performed here.
    """
    doi = _clean(record.get("doi"))
    pmid = _clean(record.get("pmid"))
    pmcid = _norm_pmcid(_clean(record.get("pmcid")))

    cache_key = doi or pmid or pmcid
    if cache is not None and cache_key and cache_key in cache:
        return dict(cache[cache_key])

    def _finish(result: dict) -> dict:
        if cache is not None and cache_key:
            cache[cache_key] = dict(result)
        return result

    # (a) existing PMCID — already a free full text, no network needed.
    if pmcid:
        return _finish({
            "fulltext_status": "fulltext_oa",
            "retrieval_method": "existing_pmcid",
            "fulltext_url": _PMC_URL.format(pmcid=pmcid),
            "pmcid": pmcid,
        })

    # Network is required for the remaining steps.
    if session is None:
        return {
            "fulltext_status": "needs_network",
            "retrieval_method": "none",
            "fulltext_url": "",
            "pmcid": "",
        }

    # (b) DOI -> Unpaywall.
    if doi and email:
        pdf = _unpaywall_pdf(doi, email, session, timeout)
        if pdf:
            return _finish({
                "fulltext_status": "fulltext_oa",
                "retrieval_method": "unpaywall",
                "fulltext_url": pdf,
                "pmcid": "",
            })

    # (c) PMID -> elink -> PMCID.
    if pmid:
        resolved = _pmcid_from_pmid(pmid, session, timeout)
        if resolved:
            return _finish({
                "fulltext_status": "fulltext_oa",
                "retrieval_method": "pmc_elink",
                "fulltext_url": _PMC_URL.format(pmcid=resolved),
                "pmcid": resolved,
            })

    # (d) no open access found -> paywall (queue for institutional access).
    return _finish({
        "fulltext_status": "paywall",
        "retrieval_method": "none",
        "fulltext_url": "",
        "pmcid": "",
    })


def resolve_many(
    records: list[dict],
    *,
    email: str | None = None,
    session: Any | None = None,
    timeout: float = 20.0,
) -> list[dict]:
    """Resolve a batch, sharing one cache. Returns records enriched in place."""
    cache: dict[str, dict] = {}
    for rec in records:
        rec.update(resolve_fulltext(rec, email=email, session=session, cache=cache, timeout=timeout))
    return records
