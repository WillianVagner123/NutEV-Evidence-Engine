"""Journal-quality scoring — a lean port of the useful core of the (removed)
local_deep_research ``journal_quality`` package.

It answers "how credible is the venue this evidence came from?" with a 1–10
score derived from bibliometric signals (h-index, DOAJ indexing, source type,
predatory flag). The heavy bits of the original (bulk S3 snapshots, a compiled
SQLite reference DB, SQLAlchemy, loguru) are replaced by a single cached
OpenAlex REST lookup, mirroring ``search/openalex_concepts.py``: fail-soft,
offline-aware, and cached on disk so repeated runs avoid the network.

``derive_quality_score`` is a pure function (no I/O) ported faithfully, so the
thresholds remain the calibrated ones from the original.
"""

from __future__ import annotations

import json
import logging
import os
import unicodedata
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# --- Calibrated thresholds (ported verbatim) -------------------------------
JOURNAL_HINDEX_ELITE = 150  # Nature/Science/NEJM tier
JOURNAL_HINDEX_STRONG = 75
JOURNAL_HINDEX_VERY_GOOD = 40
JOURNAL_HINDEX_GOOD = 20
JOURNAL_HINDEX_ACCEPTABLE = 10

JOURNAL_QUALITY_PREDATORY = 1
JOURNAL_QUALITY_DEFAULT = 4
JOURNAL_QUALITY_ACCEPTABLE = 5
JOURNAL_QUALITY_GOOD = 6
JOURNAL_QUALITY_VERY_GOOD = 7
JOURNAL_QUALITY_STRONG = 8
JOURNAL_QUALITY_ELITE = 10

DOAJ_QUALITY_WITH_SEAL = 8
DOAJ_QUALITY_NO_SEAL = 5
REPOSITORY_QUALITY_DEFAULT = 5
CONFERENCE_QUALITY_DEFAULT = 5

_CACHE_FILENAME = "journal_quality_cache.json"
_USER_AGENT = "NutEV Research Pipeline/1.0"


def normalize_name(name: str) -> str:
    """NFKC + lowercase + strip — consistent name matching."""
    return unicodedata.normalize("NFKC", str(name)).lower().strip()


def normalize_issn(issn: str) -> str:
    """Normalize an ISSN to ``XXXX-XXXX`` (uppercase, single hyphen)."""
    raw = "".join(ch for ch in str(issn).upper() if ch.isdigit() or ch == "X")
    if len(raw) == 8:
        return f"{raw[:4]}-{raw[4:]}"
    return str(issn).strip().upper()


def derive_quality_score(
    *,
    h_index: int | None = None,
    quartile: str | None = None,
    is_in_doaj: bool = False,
    has_doaj_seal: bool = False,
    is_predatory: bool = False,
    source_type: str | None = None,
) -> int | None:
    """Derive a 1–10 venue-quality score from bibliometric data (pure function).

    Order of preference: quartile (SJR-style Q1–Q4) > h-index > DOAJ indexing.
    Returns ``None`` when there is not enough signal.
    """
    if is_predatory and not is_in_doaj:
        return JOURNAL_QUALITY_PREDATORY

    # Preprint repositories aggregate non-peer-reviewed works; cap at acceptable.
    if source_type == "repository":
        return REPOSITORY_QUALITY_DEFAULT

    if quartile:
        q = quartile.upper().strip()
        q_score: int | None = None
        if q == "Q1":
            q_score = JOURNAL_QUALITY_ELITE if (h_index and h_index > JOURNAL_HINDEX_ELITE) else JOURNAL_QUALITY_STRONG
        elif q == "Q2":
            q_score = JOURNAL_QUALITY_VERY_GOOD
        elif q == "Q3":
            q_score = JOURNAL_QUALITY_GOOD
        elif q == "Q4":
            q_score = JOURNAL_QUALITY_ACCEPTABLE
        if q_score is not None:
            if has_doaj_seal:
                return max(q_score, DOAJ_QUALITY_WITH_SEAL)
            if is_in_doaj:
                return max(q_score, DOAJ_QUALITY_NO_SEAL)
            return q_score

    if h_index and h_index > 0:
        if h_index > JOURNAL_HINDEX_ELITE:
            h_score = JOURNAL_QUALITY_ELITE
        elif h_index > JOURNAL_HINDEX_STRONG:
            h_score = JOURNAL_QUALITY_STRONG
        elif h_index > JOURNAL_HINDEX_VERY_GOOD:
            h_score = JOURNAL_QUALITY_VERY_GOOD
        elif h_index > JOURNAL_HINDEX_GOOD:
            h_score = JOURNAL_QUALITY_GOOD
        elif h_index > JOURNAL_HINDEX_ACCEPTABLE:
            h_score = JOURNAL_QUALITY_ACCEPTABLE
        else:
            h_score = JOURNAL_QUALITY_DEFAULT
        if has_doaj_seal:
            return max(h_score, DOAJ_QUALITY_WITH_SEAL)
        if is_in_doaj:
            return max(h_score, DOAJ_QUALITY_NO_SEAL)
        return h_score

    if is_in_doaj:
        return DOAJ_QUALITY_WITH_SEAL if has_doaj_seal else DOAJ_QUALITY_NO_SEAL

    if source_type == "conference":
        return CONFERENCE_QUALITY_DEFAULT

    return None  # Insufficient data


# --- Cached OpenAlex source lookup -----------------------------------------
def _cache_path(config_root) -> Path:
    return Path(config_root) / _CACHE_FILENAME


def load_metrics_cache(config_root) -> dict:
    try:
        raw = json.loads(_cache_path(config_root).read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def save_metrics_cache(config_root, cache: dict) -> None:
    try:
        path = _cache_path(config_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - best-effort write
        logger.debug("failed to save journal quality cache error=%s", exc)


def fetch_journal_metrics(issn: str, *, config_root, cache: dict | None = None) -> dict:
    """Bibliometric metrics for an ISSN from OpenAlex ``/sources`` (cached, fail-soft).

    Returns ``{"h_index", "is_in_doaj", "type", "works_count", "cited_by_count"}``
    or ``{}`` when unknown/unavailable. A cached ``{"_miss": true}`` records a
    prior not-found so we do not re-hit the network.
    """
    key = normalize_issn(issn)
    if not key:
        return {}
    owns_cache = cache is None
    if cache is None:
        cache = load_metrics_cache(config_root)
    if key in cache:
        entry = cache[key]
        return {} if not isinstance(entry, dict) or entry.get("_miss") else entry

    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return {}

    metrics: dict = {"_miss": True}
    try:
        params: dict[str, object] = {}
        mailto = os.environ.get("OPENALEX_MAILTO")
        if mailto:
            params["mailto"] = mailto
        response = requests.get(
            f"https://api.openalex.org/sources/issn:{key}",
            params=params,
            timeout=(10, 30),
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
        payload = response.json()
        stats = payload.get("summary_stats") or {}
        metrics = {
            "h_index": stats.get("h_index"),
            "is_in_doaj": bool(payload.get("is_in_doaj")),
            "type": payload.get("type") or "",
            "works_count": payload.get("works_count"),
            "cited_by_count": payload.get("cited_by_count"),
        }
    except Exception as exc:
        logger.debug("journal metrics lookup failed issn=%s error=%s", key, exc)
        metrics = {"_miss": True}

    cache[key] = metrics
    if owns_cache:
        save_metrics_cache(config_root, cache)
    return {} if metrics.get("_miss") else metrics


def score_journal(issn: str, *, config_root, is_predatory: bool = False, cache: dict | None = None) -> int | None:
    """Convenience: fetch metrics for an ISSN and derive the 1–10 score (or None)."""
    metrics = fetch_journal_metrics(issn, config_root=config_root, cache=cache)
    if not metrics:
        return None
    return derive_quality_score(
        h_index=metrics.get("h_index"),
        is_in_doaj=bool(metrics.get("is_in_doaj")),
        is_predatory=is_predatory,
        source_type=metrics.get("type") or None,
    )


def enrich_journal_quality(rows: list[dict], *, config_root) -> list[dict]:
    """Annotate records with ``journal_quality_score``/``journal_in_doaj`` by ISSN.

    De-duplicates by ISSN (one network call per distinct journal), fail-soft.
    Records without an ISSN are left unchanged.
    """
    cache = load_metrics_cache(config_root)
    before = dict(cache)
    for row in rows:
        issn = str(row.get("issn") or "").strip()
        if not issn:
            continue
        metrics = fetch_journal_metrics(issn, config_root=config_root, cache=cache)
        if not metrics:
            continue
        row["journal_in_doaj"] = bool(metrics.get("is_in_doaj"))
        score = derive_quality_score(
            h_index=metrics.get("h_index"),
            is_in_doaj=bool(metrics.get("is_in_doaj")),
            source_type=metrics.get("type") or None,
        )
        if score is not None:
            row["journal_quality_score"] = score
    if cache != before:
        save_metrics_cache(config_root, cache)
    return rows
