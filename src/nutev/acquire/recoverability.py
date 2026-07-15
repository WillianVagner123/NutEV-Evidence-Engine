"""P1 — Full-text recoverability diagnostic.

Measures the *ceiling* of recoverable full text before any fetcher runs: per
workstream, how many records carry a DOI / PMID / PMCID, how many have an
open-access signal, and how many are likely paywalled. This turns "let's get
everything" into an auditable number.

The offline path uses only signals already present in the metadata (identifiers,
OpenAlex `is_open_access`/`oa_url`, a PMCID = free PMC full text). The optional
online path asks Unpaywall per DOI through an *injected* session (so it is
mockable and testable), with a simple response cache. Nothing is downloaded here
— we only measure. Configuration (the contact email) comes from the caller /
environment, never hardcoded.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable, Iterable

# Column-name candidates (matched case-insensitively) so the diagnostic works on
# either article_data.csv or metadata_master.csv without being told the schema.
_COLS = {
    "doi": ("doi",),
    "pmid": ("pmid", "pubmed_id"),
    "pmcid": ("pmcid", "pmc_id", "pmc"),
    "workstream": ("workstream", "busca", "corpus"),
    "is_open_access": ("is_open_access", "is_oa", "open_access"),
    "oa_url": ("oa_url", "open_access_url", "pmc_url"),
}


def _resolve_columns(fieldnames: Iterable[str]) -> dict[str, str | None]:
    lower = {str(f).strip().lower(): f for f in fieldnames if f}
    resolved: dict[str, str | None] = {}
    for key, candidates in _COLS.items():
        resolved[key] = next((lower[c] for c in candidates if c in lower), None)
    return resolved


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "t"}


def _clean(value: object) -> str:
    return str(value or "").strip()


def _has_offline_oa(row: dict, cols: dict[str, str | None]) -> bool:
    """OA signal available without any network call."""
    if cols["is_open_access"] and _truthy(row.get(cols["is_open_access"])):
        return True
    if cols["oa_url"] and _clean(row.get(cols["oa_url"])):
        return True
    # A PMCID means a free full-text copy exists in PMC.
    if cols["pmcid"] and _clean(row.get(cols["pmcid"])):
        return True
    return False


def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 1) if total else 0.0


# --------------------------------------------------------------------------- #
# Optional online Unpaywall check (injected session; cached).
# --------------------------------------------------------------------------- #

def unpaywall_is_oa(
    doi: str,
    email: str,
    session: Any,
    cache: dict[str, bool] | None = None,
    timeout: float = 15.0,
) -> bool:
    """Return whether Unpaywall reports an OA full text for a DOI.

    ``session`` is any object with a ``.get(url, timeout=...)`` returning an
    object with ``.status_code`` and ``.json()`` (e.g. ``requests``). Injected so
    tests can mock it and so callers control rate limiting. Results are cached by
    DOI. Any error is treated as "no OA" (conservative) rather than raising.
    """
    doi = doi.strip().lower()
    if not doi:
        return False
    if cache is not None and doi in cache:
        return cache[doi]
    ok = False
    try:
        resp = session.get(f"https://api.unpaywall.org/v2/{doi}?email={email}", timeout=timeout)
        if getattr(resp, "status_code", 0) == 200:
            data = resp.json()
            ok = bool(data.get("is_oa")) and bool(data.get("best_oa_location"))
    except Exception:
        ok = False
    if cache is not None:
        cache[doi] = ok
    return ok


def diagnose_recoverability(
    rows: list[dict],
    *,
    online: bool = False,
    email: str | None = None,
    session: Any | None = None,
    cache: dict[str, bool] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Compute recoverability per workstream and overall.

    Offline (default): counts identifier presence and offline OA signals.
    Online: additionally queries Unpaywall for records that have a DOI but no
    offline OA signal, to lift the OA estimate. Requires ``email`` and ``session``.
    """
    if not rows:
        return {"total": 0, "per_workstream": {}, "overall": {}, "online": online}
    cols = _resolve_columns(rows[0].keys())
    if online and not (email and session is not None):
        raise ValueError("online mode requires both email and session")
    if cache is None:
        cache = {}

    buckets: dict[str, dict[str, int]] = {}
    online_checks = [
        r for r in rows
        if online and cols["doi"] and _clean(r.get(cols["doi"])) and not _has_offline_oa(r, cols)
    ]
    checked = 0
    for row in rows:
        ws = _clean(row.get(cols["workstream"])) if cols["workstream"] else ""
        ws = ws or "unknown"
        b = buckets.setdefault(ws, {"total": 0, "doi": 0, "pmid": 0, "pmcid": 0, "oa": 0, "paywall": 0})
        b["total"] += 1
        has_doi = bool(cols["doi"] and _clean(row.get(cols["doi"])))
        if has_doi:
            b["doi"] += 1
        if cols["pmid"] and _clean(row.get(cols["pmid"])):
            b["pmid"] += 1
        if cols["pmcid"] and _clean(row.get(cols["pmcid"])):
            b["pmcid"] += 1
        oa = _has_offline_oa(row, cols)
        if not oa and online and has_doi:
            oa = unpaywall_is_oa(_clean(row.get(cols["doi"])), email, session, cache)  # type: ignore[arg-type]
            checked += 1
            if progress:
                progress(checked, len(online_checks))
        if oa:
            b["oa"] += 1
        else:
            b["paywall"] += 1

    per_ws = {
        ws: {
            "total": b["total"],
            "with_doi": b["doi"], "pct_doi": _pct(b["doi"], b["total"]),
            "with_pmid": b["pmid"], "pct_pmid": _pct(b["pmid"], b["total"]),
            "with_pmcid": b["pmcid"], "pct_pmcid": _pct(b["pmcid"], b["total"]),
            "open_access": b["oa"], "pct_open_access": _pct(b["oa"], b["total"]),
            "likely_paywall": b["paywall"], "pct_likely_paywall": _pct(b["paywall"], b["total"]),
        }
        for ws, b in sorted(buckets.items())
    }
    total = sum(b["total"] for b in buckets.values())
    oa_total = sum(b["oa"] for b in buckets.values())
    return {
        "total": total,
        "online": online,
        "per_workstream": per_ws,
        "overall": {
            "open_access": oa_total,
            "pct_open_access": _pct(oa_total, total),
            "likely_paywall": total - oa_total,
            "pct_likely_paywall": _pct(total - oa_total, total),
        },
    }


def read_metadata_rows(path: str | Path) -> list[dict]:
    p = Path(path)
    with p.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_recoverability_report(diagnosis: dict, out_csv: str | Path) -> Path:
    """Write the per-workstream recoverability table (tidy CSV)."""
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "workstream", "total", "with_doi", "pct_doi", "with_pmid", "pct_pmid",
        "with_pmcid", "pct_pmcid", "open_access", "pct_open_access",
        "likely_paywall", "pct_likely_paywall",
    ]
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for ws, stats in diagnosis.get("per_workstream", {}).items():
            writer.writerow({"workstream": ws, **stats})
        overall = diagnosis.get("overall", {})
        writer.writerow({
            "workstream": "TOTAL", "total": diagnosis.get("total", 0),
            "open_access": overall.get("open_access", 0),
            "pct_open_access": overall.get("pct_open_access", 0.0),
            "likely_paywall": overall.get("likely_paywall", 0),
            "pct_likely_paywall": overall.get("pct_likely_paywall", 0.0),
        })
    return out


def recoverability_summary_block(diagnosis: dict) -> dict:
    """Compact block for run_summary.json: OA vs paywall per workstream."""
    return {
        "recoverability": {
            "online": diagnosis.get("online", False),
            "total": diagnosis.get("total", 0),
            "overall_pct_open_access": diagnosis.get("overall", {}).get("pct_open_access", 0.0),
            "per_workstream_pct_open_access": {
                ws: s["pct_open_access"] for ws, s in diagnosis.get("per_workstream", {}).items()
            },
        }
    }


def _write_json(obj: dict, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return p
