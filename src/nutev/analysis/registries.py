"""Entity registries: file_asset × document_version × document_family (§7.1).

The scoping protocol's #1 rule is that a *file* is not a *document*. The same
normative document can appear as a PDF, an HTML mirror, an extracted TXT, an OCR
layer, a translation and several editions across years. Counting files as
documents is exactly how the legacy pipeline inflated its denominators.

Given the coded guide rows (each row = one physical ``file_asset`` with its
SHA-256 and provenance), this module derives:

- **document_version** — same intellectual document, same edition/year/language
  (several assets, e.g. a PDF and its HTML mirror, collapse into one version);
- **document_family** — the document across editions (the latest year is
  ``current``, older ones ``superseded`` — §18.5);
- **denominator_registry** — the named counts (assets vs versions vs families)
  so incompatible denominators are never summed or interchanged (§18.11).

Aggregators and pipeline-derived artifacts are excluded from new-unit discovery
(§8) so an aggregating spreadsheet is never counted as one document (§18.2).
Everything is deterministic and reproducible; nothing is fabricated.
"""
from __future__ import annotations

import hashlib
import re

_WS = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_YEAR = re.compile(r"\b(19|20)\d{2}\b")

# Names/kinds that must never be counted as a scientific document unit.
_AGGREGATOR_HINTS = ("all_countries", "all countries", "master_table", "master table", "aggregat", "_export")


def _clean(value: object) -> str:
    return str(value or "").strip()


def _norm(text: str) -> str:
    text = _WS.sub(" ", _NON_ALNUM.sub(" ", str(text or "").lower())).strip()
    return _WS.sub(" ", text).strip()


def _family_key(row: dict) -> str:
    """Family = country + title with the year stripped (edition-independent)."""
    country = _norm(row.get("country") or row.get("reference_country"))
    title = row.get("reference_title") or row.get("title") or row.get("name") or ""
    title_no_year = _YEAR.sub("", str(title))
    return f"{country}|{_norm(title_no_year)}".strip("|")


def _version_key(row: dict, family_key: str) -> str:
    """Version = family + edition/year + language (a translation is a new version)."""
    year = _clean(row.get("document_version") or row.get("reference_version") or row.get("year"))
    year_match = _YEAR.search(year) if year else None
    year = year_match.group(0) if year_match else year
    lang = _norm(row.get("language") or row.get("reference_language"))
    return f"{family_key}|{year}|{lang}".rstrip("|")


def _asset_sha(row: dict) -> str:
    return _clean(row.get("sha256") or row.get("archived_pdf_sha256") or row.get("reference_sha256"))


def _short_id(prefix: str, key: str, n: int = 8) -> str:
    return f"{prefix}{hashlib.sha1(key.encode('utf-8')).hexdigest()[:n].upper()}"  # noqa: S324


def is_aggregator(row: dict) -> bool:
    """Whether a row is an aggregator/derived artifact (excluded from unit counts)."""
    blob = f"{_clean(row.get('name'))} {_clean(row.get('archived_pdf_path'))} {_clean(row.get('source_url'))}".lower()
    if any(h in blob for h in _AGGREGATOR_HINTS):
        return True
    kind = _clean(row.get("fulltext_status"))
    return kind in {"aggregator"}


def _year_of(row: dict) -> int:
    m = _YEAR.search(_clean(row.get("document_version") or row.get("reference_version") or row.get("year")))
    return int(m.group(0)) if m else -1


def build_registries(rows: list[dict]) -> dict:
    """Return {file_assets, versions, families, denominators} derived from rows."""
    units = [r for r in rows if not is_aggregator(r)]

    versions: dict[str, dict] = {}
    families: dict[str, dict] = {}
    file_assets: list[dict] = []

    for row in units:
        fam_key = _family_key(row)
        ver_key = _version_key(row, fam_key)
        fam_id = _short_id("FAM", fam_key or ver_key or _asset_sha(row) or _clean(row.get("name")))
        ver_id = _short_id("VER", ver_key or fam_key or _asset_sha(row) or _clean(row.get("name")))
        sha = _asset_sha(row)
        asset_id = f"AST{sha[:10].upper()}" if sha else _short_id("AST", _clean(row.get("archived_pdf_path")) or _clean(row.get("name")))

        file_assets.append({
            "asset_id": asset_id,
            "sha256": sha,
            "kind": _clean(row.get("fulltext_status")),
            "path": _clean(row.get("archived_pdf_path")),
            "source_url": _clean(row.get("source_url") or row.get("reference_url")),
            "access_date": _clean(row.get("access_date") or row.get("reference_access_date")),
            "version_id": ver_id,
            "family_id": fam_id,
        })

        ver = versions.setdefault(ver_id, {
            "version_id": ver_id, "family_id": fam_id,
            "country": _clean(row.get("country") or row.get("reference_country")),
            "title": _clean(row.get("reference_title") or row.get("title") or row.get("name")),
            "year": _year_of(row) if _year_of(row) > 0 else "",
            "language": _clean(row.get("language") or row.get("reference_language")),
            "n_assets": 0, "asset_ids": [],
        })
        ver["n_assets"] += 1
        ver["asset_ids"].append(asset_id)

        fam = families.setdefault(fam_id, {
            "family_id": fam_id,
            "country": _clean(row.get("country") or row.get("reference_country")),
            "title": _clean(row.get("reference_title") or row.get("title") or row.get("name")),
            "version_ids": set(), "years": set(), "n_assets": 0,
        })
        fam["version_ids"].add(ver_id)
        if _year_of(row) > 0:
            fam["years"].add(_year_of(row))
        fam["n_assets"] += 1

    # Version status: within a family the max year is current, older superseded (§18.5).
    fam_max_year = {fid: (max(f["years"]) if f["years"] else None) for fid, f in families.items()}
    version_rows: list[dict] = []
    for ver in versions.values():
        maxy = fam_max_year.get(ver["family_id"])
        if isinstance(ver["year"], int) and maxy is not None:
            status = "current" if ver["year"] == maxy else "superseded"
        else:
            status = "unknown"
        version_rows.append({
            "version_id": ver["version_id"], "family_id": ver["family_id"],
            "country": ver["country"], "title": ver["title"], "year": ver["year"],
            "language": ver["language"], "status": status, "n_assets": ver["n_assets"],
            "asset_ids": "|".join(ver["asset_ids"]),
        })

    family_rows = [{
        "family_id": f["family_id"], "country": f["country"], "title": f["title"],
        "n_versions": len(f["version_ids"]), "n_assets": f["n_assets"],
        "years": "|".join(str(y) for y in sorted(f["years"])),
    } for f in families.values()]

    denominators = [
        {"name": "file_assets", "unit": "file", "n": len(file_assets),
         "note": "physical files (excludes aggregators/derived)"},
        {"name": "document_versions", "unit": "version", "n": len(version_rows),
         "note": "same document + edition/year/language"},
        {"name": "document_families", "unit": "family", "n": len(family_rows),
         "note": "document across editions"},
        {"name": "aggregators_excluded", "unit": "file", "n": len(rows) - len(units),
         "note": "aggregating/derived files not counted as documents"},
    ]
    return {
        "file_assets": file_assets,
        "versions": sorted(version_rows, key=lambda r: (r["family_id"], str(r["year"]))),
        "families": sorted(family_rows, key=lambda r: r["family_id"]),
        "denominators": denominators,
    }
