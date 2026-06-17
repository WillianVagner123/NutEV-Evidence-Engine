"""Corpus aggregations for an AI-queryable article knowledge base.

Pure standard library (``csv``, ``json``, ``collections``). No pandas.

Given a list of "knowledge base records" (see the input contract below), this
module computes deterministic corpus-level aggregations answering questions such
as "what is each country saying", "where is it published", "which concepts show
up where". All output is sorted deterministically with ties broken
alphabetically so re-running on the same input yields byte-identical files.

Input contract -- each record is a ``dict`` with (any field may be missing,
``None`` or the wrong type; everything is coerced defensively)::

    document_id:str, workstream:str, title:str, abstract:str, authors:str,
    year:int|None, language:str (ISO-639-1; "" if unknown),
    countries:list[str] (ISO alpha-2; may be []), region:str,
    journal:str, issn:str, publisher:str, doi:str, url:str,
    source_providers:list[str], domains:list[str], outcomes:list[str],
    diet_patterns:list[str], clinical_conditions:list[str],
    evidence_type:str, evidence_tier:str, relevance_score:int|float,
    cited_by_count:int
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

__all__ = ["write_aggregations"]


# ---------------------------------------------------------------------------
# Defensive coercion helpers
# ---------------------------------------------------------------------------
def _as_str(value: Any) -> str:
    """Coerce ``value`` to a stripped string; ``None`` -> ``""``."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _as_str_list(value: Any) -> list[str]:
    """Coerce ``value`` to a list of non-empty stripped strings.

    Accepts an existing list/tuple/set of arbitrary items, or a scalar
    (wrapped into a single-element list). Empty/blank entries are dropped.
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        items = list(value)
    elif isinstance(value, str):
        items = [value]
    else:
        items = [value]
    out: list[str] = []
    for item in items:
        s = _as_str(item)
        if s:
            out.append(s)
    return out


def _as_year(value: Any) -> int | None:
    """Coerce ``value`` to an ``int`` year, or ``None`` if not parseable."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value == value else None  # reject NaN
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            # tolerate things like "2021-05" or "2021.0"
            head = s.replace(".", "-").split("-", 1)[0].strip()
            try:
                return int(head)
            except ValueError:
                return None
    return None


def _countries_of(record: dict) -> list[str]:
    """Return the country codes for a record; empty -> ``[""]`` sentinel."""
    codes = _as_str_list(record.get("countries"))
    # Normalise to upper-case alpha-2-ish codes for stable grouping.
    codes = [c.upper() for c in codes]
    # De-duplicate within a single document while preserving determinism;
    # a doc listing the same country twice should only count once per doc.
    seen: list[str] = []
    for code in codes:
        if code not in seen:
            seen.append(code)
    return seen if seen else [""]


# ---------------------------------------------------------------------------
# Top-N formatting
# ---------------------------------------------------------------------------
def _top(counter: Counter, n: int = 5) -> str:
    """Return a ``";"``-joined ``"term(count)"`` string for the ``n`` most common.

    Ordering is by count descending, ties broken alphabetically by term so the
    output is fully deterministic. Empty terms are skipped.
    """
    items = [(term, count) for term, count in counter.items() if _as_str(term)]
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    return ";".join(f"{term}({count})" for term, count in items[:n])


def _top_pairs(counter: Counter, n: int) -> list[list]:
    """Return the top ``n`` ``[term, count]`` pairs (count desc, then term asc)."""
    items = [(term, count) for term, count in counter.items() if _as_str(term)]
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    return [[term, count] for term, count in items[:n]]


def _most_common_single(counter: Counter) -> str:
    """Return the single most common non-empty term (ties alphabetical), or ``""``."""
    items = [(term, count) for term, count in counter.items() if _as_str(term)]
    if not items:
        return ""
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    return items[0][0]


# ---------------------------------------------------------------------------
# CSV / JSON writers
# ---------------------------------------------------------------------------
def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def _write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
_CONCEPT_FIELDS = (
    ("domain", "domains"),
    ("outcome", "outcomes"),
    ("diet_pattern", "diet_patterns"),
    ("clinical_condition", "clinical_conditions"),
)


def write_aggregations(records: list[dict], out_dir: Path) -> dict[str, Path]:
    """Compute corpus aggregations and write them into ``out_dir``.

    Writes six files and returns a mapping of logical name -> :class:`Path`:

    * ``by_country.csv`` -- one row per country code. A document listing two
      countries counts in *both* rows. Docs with no countries are grouped under
      the empty code and written as ``"UNKNOWN"``.
      Columns: ``country, n_docs, top_domains, top_outcomes, top_diet_patterns,
      top_conditions, top_journals, languages``. Sorted by ``n_docs`` desc then
      ``country`` asc.
    * ``by_venue.csv`` -- one row per non-empty journal.
      Columns: ``journal, n_docs, country, issn, publisher, top_domains``
      (``country`` is the single most common country for that journal). Sorted
      by ``n_docs`` desc then ``journal`` asc.
    * ``by_language.csv`` -- columns: ``language, n_docs, top_countries,
      top_domains`` (``""`` language -> ``"unknown"``). Sorted by ``n_docs``
      desc then ``language`` asc.
    * ``by_year.csv`` -- columns: ``year, n_docs, top_domains``. ``None`` years
      are skipped. Sorted by ``year`` asc.
    * ``by_concept.csv`` -- long format. Columns: ``concept_type, concept,
      n_docs, top_countries`` with ``concept_type`` in
      ``{domain, outcome, diet_pattern, clinical_condition}``; one row per
      ``(type, concept)``. Sorted by ``concept_type`` asc then ``n_docs`` desc
      (ties: ``concept`` asc).
    * ``overview.json`` -- corpus summary object.

    :param records: list of knowledge base records (any field may be missing or
        wrongly typed; values are coerced defensively).
    :param out_dir: directory to write into (created with parents if needed).
    :returns: ``{name: Path}`` for the six written files.
    """
    records = list(records or [])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- per-country accumulators ------------------------------------------
    country_n: Counter = Counter()
    country_domains: dict[str, Counter] = {}
    country_outcomes: dict[str, Counter] = {}
    country_diets: dict[str, Counter] = {}
    country_conditions: dict[str, Counter] = {}
    country_journals: dict[str, Counter] = {}
    country_languages: dict[str, Counter] = {}

    # --- per-venue accumulators --------------------------------------------
    venue_n: Counter = Counter()
    venue_countries: dict[str, Counter] = {}
    venue_issn: dict[str, str] = {}
    venue_publisher: dict[str, str] = {}
    venue_domains: dict[str, Counter] = {}

    # --- per-language accumulators -----------------------------------------
    language_n: Counter = Counter()
    language_countries: dict[str, Counter] = {}
    language_domains: dict[str, Counter] = {}

    # --- per-year accumulators ---------------------------------------------
    year_n: Counter = Counter()
    year_domains: dict[int, Counter] = {}

    # --- per-concept accumulators ------------------------------------------
    # concept_n[(type, concept)] = n_docs ; concept_countries[...] = Counter
    concept_n: Counter = Counter()
    concept_countries: dict[tuple[str, str], Counter] = {}

    # --- corpus-wide accumulators ------------------------------------------
    total_countries: Counter = Counter()
    total_journals: Counter = Counter()
    total_languages: Counter = Counter()
    total_domains: Counter = Counter()
    total_outcomes: Counter = Counter()
    total_diets: Counter = Counter()
    total_conditions: Counter = Counter()
    total_providers: Counter = Counter()
    years_seen: list[int] = []

    def _bump(table: dict, key, terms: list[str]) -> None:
        counter = table.get(key)
        if counter is None:
            counter = Counter()
            table[key] = counter
        counter.update(terms)

    for record in records:
        if not isinstance(record, dict):
            record = {}

        codes = _countries_of(record)  # at least [""]
        real_codes = [c for c in codes if c]  # excludes the unknown sentinel
        domains = _as_str_list(record.get("domains"))
        outcomes = _as_str_list(record.get("outcomes"))
        diets = _as_str_list(record.get("diet_patterns"))
        conditions = _as_str_list(record.get("clinical_conditions"))
        journal = _as_str(record.get("journal"))
        issn = _as_str(record.get("issn"))
        publisher = _as_str(record.get("publisher"))
        language = _as_str(record.get("language"))
        year = _as_year(record.get("year"))
        providers = _as_str_list(record.get("source_providers"))

        # ---- country aggregation (counts in EVERY listed country) ---------
        for code in codes:
            country_n[code] += 1
            if domains:
                _bump(country_domains, code, domains)
            if outcomes:
                _bump(country_outcomes, code, outcomes)
            if diets:
                _bump(country_diets, code, diets)
            if conditions:
                _bump(country_conditions, code, conditions)
            if journal:
                _bump(country_journals, code, [journal])
            # languages counter keyed by language label ("unknown" if blank)
            _bump(country_languages, code, [language or "unknown"])

        # ---- venue aggregation -------------------------------------------
        if journal:
            venue_n[journal] += 1
            if real_codes:
                _bump(venue_countries, journal, real_codes)
            # first non-empty issn / publisher wins, deterministic by input order
            if issn and not venue_issn.get(journal):
                venue_issn[journal] = issn
            if publisher and not venue_publisher.get(journal):
                venue_publisher[journal] = publisher
            if domains:
                _bump(venue_domains, journal, domains)

        # ---- language aggregation ----------------------------------------
        lang_key = language or ""
        language_n[lang_key] += 1
        if real_codes:
            _bump(language_countries, lang_key, real_codes)
        if domains:
            _bump(language_domains, lang_key, domains)

        # ---- year aggregation --------------------------------------------
        if year is not None:
            year_n[year] += 1
            if domains:
                _bump(year_domains, year, domains)
            years_seen.append(year)

        # ---- concept aggregation (long format) ---------------------------
        for concept_type, field in _CONCEPT_FIELDS:
            for concept in _as_str_list(record.get(field)):
                key = (concept_type, concept)
                concept_n[key] += 1
                if real_codes:
                    _bump(concept_countries, key, real_codes)

        # ---- corpus-wide -------------------------------------------------
        total_countries.update(real_codes)
        if journal:
            total_journals[journal] += 1
        total_languages[language or "unknown"] += 1
        total_domains.update(domains)
        total_outcomes.update(outcomes)
        total_diets.update(diets)
        total_conditions.update(conditions)
        total_providers.update(providers)

    paths: dict[str, Path] = {}

    # --- by_country.csv ----------------------------------------------------
    country_rows: list[list] = []
    for code, n_docs in country_n.items():
        country_rows.append(
            [
                "UNKNOWN" if code == "" else code,
                n_docs,
                _top(country_domains.get(code, Counter())),
                _top(country_outcomes.get(code, Counter())),
                _top(country_diets.get(code, Counter())),
                _top(country_conditions.get(code, Counter())),
                _top(country_journals.get(code, Counter())),
                _top(country_languages.get(code, Counter())),
            ]
        )
    # sort by n_docs desc, then country label asc
    country_rows.sort(key=lambda r: (-r[1], r[0]))
    by_country = out_dir / "by_country.csv"
    _write_csv(
        by_country,
        [
            "country",
            "n_docs",
            "top_domains",
            "top_outcomes",
            "top_diet_patterns",
            "top_conditions",
            "top_journals",
            "languages",
        ],
        country_rows,
    )
    paths["by_country"] = by_country

    # --- by_venue.csv ------------------------------------------------------
    venue_rows: list[list] = []
    for journal, n_docs in venue_n.items():
        venue_rows.append(
            [
                journal,
                n_docs,
                _most_common_single(venue_countries.get(journal, Counter())),
                venue_issn.get(journal, ""),
                venue_publisher.get(journal, ""),
                _top(venue_domains.get(journal, Counter())),
            ]
        )
    venue_rows.sort(key=lambda r: (-r[1], r[0]))
    by_venue = out_dir / "by_venue.csv"
    _write_csv(
        by_venue,
        ["journal", "n_docs", "country", "issn", "publisher", "top_domains"],
        venue_rows,
    )
    paths["by_venue"] = by_venue

    # --- by_language.csv ---------------------------------------------------
    language_rows: list[list] = []
    for lang_key, n_docs in language_n.items():
        language_rows.append(
            [
                "unknown" if lang_key == "" else lang_key,
                n_docs,
                _top(language_countries.get(lang_key, Counter())),
                _top(language_domains.get(lang_key, Counter())),
            ]
        )
    language_rows.sort(key=lambda r: (-r[1], r[0]))
    by_language = out_dir / "by_language.csv"
    _write_csv(
        by_language,
        ["language", "n_docs", "top_countries", "top_domains"],
        language_rows,
    )
    paths["by_language"] = by_language

    # --- by_year.csv -------------------------------------------------------
    year_rows: list[list] = []
    for year, n_docs in year_n.items():
        year_rows.append(
            [year, n_docs, _top(year_domains.get(year, Counter()))]
        )
    year_rows.sort(key=lambda r: r[0])  # year asc; None years already skipped
    by_year = out_dir / "by_year.csv"
    _write_csv(by_year, ["year", "n_docs", "top_domains"], year_rows)
    paths["by_year"] = by_year

    # --- by_concept.csv ----------------------------------------------------
    concept_rows: list[list] = []
    for (concept_type, concept), n_docs in concept_n.items():
        concept_rows.append(
            [
                concept_type,
                concept,
                n_docs,
                _top(concept_countries.get((concept_type, concept), Counter())),
            ]
        )
    # concept_type asc, then n_docs desc, ties by concept asc
    concept_rows.sort(key=lambda r: (r[0], -r[2], r[1]))
    by_concept = out_dir / "by_concept.csv"
    _write_csv(
        by_concept,
        ["concept_type", "concept", "n_docs", "top_countries"],
        concept_rows,
    )
    paths["by_concept"] = by_concept

    # --- overview.json -----------------------------------------------------
    year_min = min(years_seen) if years_seen else None
    year_max = max(years_seen) if years_seen else None
    overview = {
        "n_documents": len(records),
        "n_countries": len(total_countries),
        "n_journals": len(total_journals),
        "n_languages": len([lang for lang in total_languages if lang != "unknown"]),
        "year_min": year_min,
        "year_max": year_max,
        "providers": dict(total_providers),
        "top_countries": _top_pairs(total_countries, 15),
        "top_journals": _top_pairs(total_journals, 15),
        "top_domains": _top_pairs(total_domains, 15),
        "top_outcomes": _top_pairs(total_outcomes, 15),
        "top_diet_patterns": _top_pairs(total_diets, 15),
        "top_conditions": _top_pairs(total_conditions, 15),
        "languages": dict(total_languages),
    }
    overview_path = out_dir / "overview.json"
    _write_json(overview_path, overview)
    paths["overview"] = overview_path

    return paths
