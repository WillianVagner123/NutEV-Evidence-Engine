"""Predatory-venue detection — lean port of LDR's "Stop Predatory Journals" source.

Two layers, both fail-soft and offline-aware:

- an editable overlay at ``config/predatory_journals.json`` (always consulted,
  works fully offline — the user owns it);
- the public **Stop Predatory Journals** list (MIT, the community successor to
  Beall's List), fetched once and cached under ``config_root`` as
  ``predatory_index.json`` when the network is available.

Matching is by NFKC-normalized name (journal or publisher) or by ISSN. Heavy
LDR machinery (SQLite, loguru, safe_requests, bulk snapshots) is dropped.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from pathlib import Path

import requests

from nutev.analysis.journal_quality import normalize_issn, normalize_name

logger = logging.getLogger(__name__)

OVERLAY_FILENAME = "predatory_journals.json"
_CACHE_FILENAME = "predatory_index.json"
_USER_AGENT = "NutEV Research Pipeline/1.0"
_PREDATORY_BASE = (
    "https://raw.githubusercontent.com/stop-predatory-journals/"
    "stop-predatory-journals.github.io/master/_data"
)
_PREDATORY_FILES = ("publishers.csv", "journals.csv", "hijacked.csv")
# Safety floor (mirrors LDR): refuse a near-empty payload from a partial outage.
_MIN_PREDATORY_TOTAL = 100


def load_overlay(config_root) -> dict:
    """Read the editable ``config/predatory_journals.json`` overlay."""
    empty = {"names": set(), "issns": set()}
    try:
        raw = json.loads((Path(config_root) / OVERLAY_FILENAME).read_text(encoding="utf-8"))
    except Exception:
        return empty
    if not isinstance(raw, dict):
        return empty
    names = {normalize_name(v) for key in ("publishers", "journals", "names") for v in (raw.get(key) or [])}
    names.discard("")
    issns = {normalize_issn(v) for v in (raw.get("issns") or []) if str(v).strip()}
    return {"names": names, "issns": issns}


def _fetch_spj() -> dict | None:
    """Fetch + merge the three public Stop Predatory Journals CSVs (fail-soft)."""
    names: set[str] = set()
    issns: set[str] = set()
    try:
        for fname in _PREDATORY_FILES:
            resp = requests.get(
                f"{_PREDATORY_BASE}/{fname}",
                timeout=(10, 30),
                headers={"User-Agent": _USER_AGENT},
            )
            resp.raise_for_status()
            for row in csv.DictReader(io.StringIO(resp.text)):
                name = normalize_name(row.get("name") or row.get("title") or "")
                if name:
                    names.add(name)
                for key, value in row.items():
                    if value and "issn" in (key or "").lower():
                        nv = normalize_issn(value)
                        if len(nv) == 9:  # XXXX-XXXX
                            issns.add(nv)
    except Exception as exc:
        logger.debug("predatory list fetch failed error=%s", exc)
        return None
    if len(names) < _MIN_PREDATORY_TOTAL:
        return None
    return {"names": sorted(names), "issns": sorted(issns)}


def load_predatory_index(config_root) -> dict:
    """Build the predatory index = editable overlay ∪ cached/fetched SPJ list."""
    overlay = load_overlay(config_root)
    names: set[str] = set(overlay["names"])
    issns: set[str] = set(overlay["issns"])

    cache_path = Path(config_root) / _CACHE_FILENAME
    spj: dict | None = None
    try:
        spj = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        spj = None
    if spj is None and os.environ.get("NUTEV_DISABLE_NETWORK") != "1":
        spj = _fetch_spj()
        if spj is not None:
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(spj, ensure_ascii=False), encoding="utf-8")
            except Exception as exc:  # pragma: no cover - best-effort write
                logger.debug("failed to save predatory index error=%s", exc)
    if isinstance(spj, dict):
        names.update(normalize_name(n) for n in spj.get("names", []))
        issns.update(normalize_issn(i) for i in spj.get("issns", []))
    names.discard("")
    return {"names": names, "issns": issns}


def is_predatory(*, journal=None, publisher=None, issn=None, index: dict) -> bool:
    """True if the venue's name/publisher/ISSN appears in the predatory index."""
    names = index.get("names") or set()
    issns = index.get("issns") or set()
    for candidate in (journal, publisher):
        if candidate and normalize_name(candidate) in names:
            return True
    return bool(issn and normalize_issn(issn) in issns)
