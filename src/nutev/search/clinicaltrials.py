"""ClinicalTrials.gov study-search connector (API v2).

Adds clinical-trial registry evidence (distinct from journal articles) via the
public ClinicalTrials.gov v2 REST API — no key required. Same connector contract
as the bibliographic providers: normalization to the shared row schema,
timeout + exponential backoff, a reproducible single-page default and opt-in
bounded pagination (cursor-based via ``nextPageToken``).
"""
from __future__ import annotations

import os
import re
import time
from typing import Any

import requests

_CTGOV_URL = "https://clinicaltrials.gov/api/v2/studies"
_YEAR_RE = re.compile(r"(19|20)\d{2}")


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _year(date_str: str) -> str:
    match = _YEAR_RE.search(_clean(date_str))
    return match.group(0) if match else ""


def _normalize_study(study: dict, query: str) -> dict:
    protocol = study.get("protocolSection", {}) if isinstance(study, dict) else {}
    ident = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    desc = protocol.get("descriptionModule", {})
    sponsor = (protocol.get("sponsorCollaboratorsModule", {}) or {}).get("leadSponsor", {})
    nct_id = _clean(ident.get("nctId"))
    summary = _clean(desc.get("briefSummary"))
    return {
        "source": "clinicaltrials",
        "source_provider": "clinicaltrials",
        "title": _clean(ident.get("briefTitle") or ident.get("officialTitle")),
        "abstract": summary,
        "snippet": summary,
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "registry_id": nct_id,
        "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
        "journal": "ClinicalTrials.gov",
        "year": _year((status.get("startDateStruct", {}) or {}).get("date")),
        "publication_date": _clean((status.get("startDateStruct", {}) or {}).get("date")),
        "article_type": "clinical_trial",
        "authors": "",
        "source_institution": _clean(sponsor.get("name")),
        "metadata_status": "clinicaltrials_search",
        "query": query,
        "provider_query": query,
    }


def _ctgov_get(query: str, page_size: int, page_token: str | None) -> dict | None:
    """GET one page with exponential backoff. Returns parsed JSON or None."""
    params: dict[str, Any] = {"query.term": query, "pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token
    for attempt in range(1, 4):
        try:
            response = requests.get(
                _CTGOV_URL,
                params=params,
                timeout=45,
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            time.sleep(min(2 ** attempt, 8))
    return None


def _resolve_max_results(page_size: int, max_results: int | None) -> int:
    """Default (None) preserves single-page behaviour; opt into deeper recall with
    NUTEV_CLINICALTRIALS_MAX_RESULTS so default runs stay reproducible."""
    if max_results is not None:
        return max(max_results, 0)
    env = os.environ.get("NUTEV_CLINICALTRIALS_MAX_RESULTS", "")
    return int(env) if env.isdigit() and int(env) > 0 else page_size


def search_clinicaltrials(query: str, page_size: int = 18, max_results: int | None = None) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    if os.environ.get("NUTEV_SKIP_CLINICALTRIALS") == "1":
        return []

    page_size = max(1, min(page_size, 1000))  # ClinicalTrials.gov v2 caps at 1000
    target = _resolve_max_results(page_size, max_results)

    # Single-page path — kept simple and reproducible.
    if target <= page_size:
        data = _ctgov_get(query, page_size, None)
        if not data:
            return []
        return [_normalize_study(s, query) for s in data.get("studies", []) or []]

    # Paginated path — nextPageToken cursor walk up to `target`, de-duplicating by NCT id.
    collected: list[dict] = []
    seen: set[str] = set()
    token: str | None = None
    while len(collected) < target:
        data = _ctgov_get(query, min(page_size, target - len(collected)), token)
        if not data:
            break
        studies = data.get("studies", []) or []
        if not studies:
            break
        for study in studies:
            row = _normalize_study(study, query)
            key = row["registry_id"] or row["title"]
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            collected.append(row)
            if len(collected) >= target:
                break
        token = data.get("nextPageToken")
        if not token:
            break
    return collected
