"""Article 1 reports: the Domain Integration Matrix and the two-track PRISMA.

The Integration Matrix is the central artifact of the scoping review: it turns
"the literature is fragmented" from an opinion into data by measuring how the
A/B/C/D analytical domains are (co-)covered across the corpus.

Records passed in may already carry the Article-1 fields (``domain_A`` … ``track``)
or not; missing fields are computed on the fly via
:mod:`nutev.analysis.article1_coding`, so callers can pass raw curated rows.
"""
from __future__ import annotations

import csv
from pathlib import Path

from nutev.analysis.article1_coding import (
    PRISMA_DATABASE_TRACK,
    classify_track,
    code_context_flags,
    code_domains,
)

_DOMAINS = ("A", "B", "C", "D")


def _ensure_coded(record: dict) -> dict:
    """Return a record guaranteed to carry domain/track/context fields."""
    out = dict(record)
    if not all(f"domain_{d}" in out for d in _DOMAINS):
        out.update(code_domains(record))
    if "track" not in out:
        out["track"] = classify_track(record)
    if "mentions_cost" not in out or "mentions_equity" not in out:
        out.update(code_context_flags(record))
    return out


def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 1) if total else 0.0


def _track_layer(track: str) -> str:
    """Map a track to the analytical layer used in the by-layer breakdown."""
    if track in ("guideline_repository",):
        return "guias"
    if track in ("indexed_database", "society_website"):
        return "diretrizes"
    if track in ("linked_implementation_material",):
        return "materiais_implementacao"
    return "outros"


def build_integration_matrix(records: list[dict]) -> dict:
    """Compute the four-block Domain Integration Matrix.

    Returns a dict with ``domain_coverage``, ``profile_distribution``,
    ``by_layer`` and ``markers`` blocks, plus ``total`` and the headline metrics
    (``documents_with_all_four_domains``).
    """
    coded = [_ensure_coded(r) for r in records]
    total = len(coded)

    # Block 1 — coverage per domain.
    domain_coverage = {}
    for d in _DOMAINS:
        n = sum(1 for r in coded if r.get(f"domain_{d}"))
        domain_coverage[d] = {"n": n, "pct": _pct(n, total)}

    # Block 2 — profile distribution.
    profiles: dict[str, int] = {}
    for r in coded:
        prof = r.get("profile") or "".join(d for d in _DOMAINS if r.get(f"domain_{d}")) or "none"
        profiles[prof] = profiles.get(prof, 0) + 1
    profile_distribution = {
        prof: {"n": n, "pct": _pct(n, total)}
        for prof, n in sorted(profiles.items(), key=lambda kv: (-kv[1], kv[0]))
    }

    # Block 3 — breakdown by layer (guias × diretrizes × materiais de implementação).
    by_layer: dict[str, dict] = {}
    for r in coded:
        layer = _track_layer(r.get("track", ""))
        entry = by_layer.setdefault(layer, {"n": 0, **{d: 0 for d in _DOMAINS}})
        entry["n"] += 1
        for d in _DOMAINS:
            if r.get(f"domain_{d}"):
                entry[d] += 1

    # Block 4 — markers.
    n_cost = sum(1 for r in coded if r.get("mentions_cost"))
    n_equity = sum(1 for r in coded if r.get("mentions_equity"))
    # "menciona custo E oferece estratégia" — cost mentioned in a document that is
    # also substantive on domain D (adherence/implementation strategy).
    n_cost_and_strategy = sum(1 for r in coded if r.get("mentions_cost") and r.get("domain_D"))
    markers = {
        "mentions_cost": {"n": n_cost, "pct": _pct(n_cost, total)},
        "mentions_equity": {"n": n_equity, "pct": _pct(n_equity, total)},
        "mentions_cost_and_offers_strategy": {"n": n_cost_and_strategy, "pct": _pct(n_cost_and_strategy, total)},
    }

    all_four = sum(1 for r in coded if all(r.get(f"domain_{d}") for d in _DOMAINS))
    return {
        "total": total,
        "domain_coverage": domain_coverage,
        "profile_distribution": profile_distribution,
        "by_layer": by_layer,
        "markers": markers,
        "documents_with_all_four_domains": all_four,
    }


def _matrix_rows(matrix: dict) -> list[dict]:
    """Flatten the matrix into a tidy [block, category, n, pct] CSV shape."""
    rows: list[dict] = []
    for d, v in matrix["domain_coverage"].items():
        rows.append({"block": "domain_coverage", "category": d, "n": v["n"], "pct": v["pct"]})
    for prof, v in matrix["profile_distribution"].items():
        rows.append({"block": "profile_distribution", "category": prof, "n": v["n"], "pct": v["pct"]})
    for layer, v in matrix["by_layer"].items():
        rows.append({"block": "by_layer", "category": f"{layer}|n", "n": v["n"], "pct": _pct(v["n"], matrix["total"])})
        for d in _DOMAINS:
            rows.append({"block": "by_layer", "category": f"{layer}|{d}", "n": v[d], "pct": _pct(v[d], v["n"] or 1)})
    for key, v in matrix["markers"].items():
        rows.append({"block": "markers", "category": key, "n": v["n"], "pct": v["pct"]})
    return rows


def write_integration_matrix(records: list[dict], tables_dir: Path) -> dict:
    """Write ``NUTEV_DOMAIN_INTEGRATION_MATRIX.csv`` and return run-summary fields.

    The returned dict is meant to be merged into ``run_summary.json``:
    ``domain_coverage``, ``profile_distribution`` and
    ``documents_with_all_four_domains``.
    """
    tables_dir = Path(tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    matrix = build_integration_matrix(records)

    out = tables_dir / "NUTEV_DOMAIN_INTEGRATION_MATRIX.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["block", "category", "n", "pct"])
        writer.writeheader()
        writer.writerows(_matrix_rows(matrix))

    return {
        "domain_coverage": {d: v["n"] for d, v in matrix["domain_coverage"].items()},
        "profile_distribution": {p: v["n"] for p, v in matrix["profile_distribution"].items()},
        "documents_with_all_four_domains": matrix["documents_with_all_four_domains"],
    }


def build_two_track_prisma(records: list[dict]) -> dict:
    """PRISMA 2020 identification split: databases/registers vs other methods.

    Returns counts for the two identification columns the PRISMA-ScR flow requires,
    plus a per-track breakdown of the "other methods" column.
    """
    coded = [_ensure_coded(r) for r in records]
    from_databases = sum(1 for r in coded if r.get("track") == PRISMA_DATABASE_TRACK)
    other_methods = len(coded) - from_databases
    by_track: dict[str, int] = {}
    for r in coded:
        t = r.get("track", "")
        by_track[t] = by_track.get(t, 0) + 1
    return {
        "identified_from_databases": from_databases,
        "identified_from_other_methods": other_methods,
        "by_track": by_track,
    }
