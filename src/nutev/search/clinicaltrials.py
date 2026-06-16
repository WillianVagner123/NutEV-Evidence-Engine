from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\b(\d{4})\b")


def _clean_text(value: Any | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _extract_year(*values: Any | None) -> str:
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        match = _YEAR_RE.search(text)
        if match:
            return match.group(1)
    return ""


def _normalize_clinicaltrials(study: dict, query: str) -> dict:
    """Map one ClinicalTrials.gov API v2 study object to the pipeline row schema.

    Pure function: no network or environment access. Every schema key is always
    present, defaulting to "" when the source field is missing.
    """
    protocol = study.get("protocolSection") or {}
    identification = protocol.get("identificationModule") or {}
    description = protocol.get("descriptionModule") or {}
    status = protocol.get("statusModule") or {}
    design = protocol.get("designModule") or {}
    sponsors = protocol.get("sponsorCollaboratorsModule") or {}
    conditions_module = protocol.get("conditionsModule") or {}

    nct_id = _clean_text(identification.get("nctId"))
    title = _clean_text(identification.get("briefTitle"))
    brief_summary = _clean_text(description.get("briefSummary"))

    start_date = _clean_text((status.get("startDateStruct") or {}).get("date"))
    first_post_date = _clean_text((status.get("studyFirstPostDateStruct") or {}).get("date"))

    study_type = _clean_text(design.get("studyType"))
    lead_sponsor = _clean_text((sponsors.get("leadSponsor") or {}).get("name"))

    conditions = conditions_module.get("conditions") or []
    conditions = [_clean_text(c) for c in conditions if _clean_text(c)] if isinstance(conditions, list) else []

    abstract = brief_summary
    if conditions:
        condition_context = "Conditions: " + ", ".join(conditions)
        abstract = f"{abstract}\n\n{condition_context}" if abstract else condition_context

    snippet = brief_summary[:300]

    url = f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else ""

    return {
        "source": "clinicaltrials",
        "source_provider": "clinicaltrials",
        "title": title,
        "abstract": abstract,
        "snippet": snippet,
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "url": url,
        "journal": "ClinicalTrials.gov",
        "year": _extract_year(start_date, first_post_date),
        "publication_date": start_date or first_post_date,
        "article_type": study_type,
        "authors": lead_sponsor,
        "metadata_status": "clinicaltrials_search",
        "query": query,
        "provider_query": query,
        "oa_pdf_url": "",
        "is_open_access": "true",
    }


def search_clinicaltrials(query: str, *, limit: int = 20, context: dict | None = None) -> list[dict]:
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []

    last: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = requests.get(
                "https://clinicaltrials.gov/api/v2/studies",
                params={"query.term": query, "pageSize": min(limit, 100), "format": "json"},
                timeout=(10, 30),
                headers={"User-Agent": "NutEV Research Pipeline/1.0"},
            )
            if response.status_code == 429 or response.status_code >= 500:
                raise RuntimeError(f"ClinicalTrials.gov HTTP {response.status_code}")
            response.raise_for_status()
            payload = response.json()
            rows = [_normalize_clinicaltrials(s, query) for s in payload.get("studies", [])]
            return rows
        except Exception as exc:
            last = exc
            time.sleep(1.0 * attempt)

    logger.warning("clinicaltrials search failed query=%s error=%s", query, last)
    return []
