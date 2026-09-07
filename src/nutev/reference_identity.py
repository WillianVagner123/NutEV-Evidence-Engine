from __future__ import annotations

import re
import unicodedata
from itertools import combinations
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
_PMID_RE = re.compile(r"^[0-9]{1,9}$")
_PMCID_RE = re.compile(r"^PMC[0-9]+$", re.I)
_SPACE_RE = re.compile(r"\s+")


def normalize_doi(value: Any) -> str:
    """Return a canonical DOI only when its syntax is plausible."""

    raw = str(value or "").strip()
    if not raw:
        return ""
    lowered = raw.casefold()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if lowered.startswith(prefix):
            raw = raw[len(prefix) :].strip()
            break
    raw = raw.rstrip(" .;,)]}")
    if not _DOI_RE.fullmatch(raw):
        return ""
    return raw.casefold()


def valid_doi(value: Any) -> bool:
    return bool(normalize_doi(value))


def normalize_pmid(value: Any) -> str:
    """Return a PMID only when the complete supplied value is valid."""

    raw = str(value or "").strip()
    return raw if raw and _PMID_RE.fullmatch(raw) else ""


def valid_pmid(value: Any) -> bool:
    return bool(normalize_pmid(value))


def normalize_pmcid(value: Any) -> str:
    raw = str(value or "").strip()
    return raw.upper() if raw and _PMCID_RE.fullmatch(raw) else ""


def valid_pmcid(value: Any) -> bool:
    return bool(normalize_pmcid(value))


def normalize_url(value: Any) -> str:
    """Normalize a traceable HTTP(S) URL; invalid schemes return blank."""

    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except Exception:
        return ""
    if parts.scheme.casefold() not in {"http", "https"} or not parts.netloc:
        return ""
    host = parts.netloc.casefold().removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.casefold(), host, path, parts.query, ""))


def normalize_title(value: Any) -> str:
    """Conservative exact-title fallback: Unicode normalize, casefold, collapse spaces."""

    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return _SPACE_RE.sub(" ", text)


def valid_identifier_kind(row: dict[str, Any]) -> str:
    """Return the first valid primary identifier kind without inferring repairs."""

    if normalize_doi(row.get("doi") or row.get("doi_normalized")):
        return "doi"
    if normalize_pmid(row.get("pmid") or row.get("pmid_normalized")):
        return "pmid"
    if normalize_pmcid(row.get("pmcid")):
        return "pmcid"
    return ""


def has_valid_identifier(row: dict[str, Any]) -> bool:
    return bool(valid_identifier_kind(row))


def canonical_identity(row: dict[str, Any]) -> str:
    """Canonical cross-stage identity: DOI -> PMID -> HTTP(S) URL -> title."""

    doi = normalize_doi(row.get("doi") or row.get("doi_normalized"))
    if doi:
        return "doi:" + doi
    pmid = normalize_pmid(row.get("pmid") or row.get("pmid_normalized"))
    if pmid:
        return "pmid:" + pmid
    url = normalize_url(row.get("url") or row.get("url_normalized"))
    if url:
        return "url:" + url.casefold()
    title = normalize_title(row.get("title"))
    return "title:" + title if title else ""


def _exact_identity_aliases(row: dict[str, Any]) -> tuple[str, ...]:
    """Return only exact observed aliases; title is fallback only when no exact alias exists."""

    aliases: list[str] = []
    doi = normalize_doi(row.get("doi") or row.get("doi_normalized"))
    pmid = normalize_pmid(row.get("pmid") or row.get("pmid_normalized"))
    pmcid = normalize_pmcid(row.get("pmcid"))
    url = normalize_url(row.get("url") or row.get("url_normalized"))
    if doi:
        aliases.append("doi:" + doi)
    if pmid:
        aliases.append("pmid:" + pmid)
    if pmcid:
        aliases.append("pmcid:" + pmcid.casefold())
    if url:
        aliases.append("url:" + url.casefold())
    if aliases:
        return tuple(dict.fromkeys(aliases))
    title = normalize_title(row.get("title"))
    return ("title:" + title,) if title else ()


def _provider_name(row: dict[str, Any]) -> str:
    return str(row.get("source_provider") or row.get("provider") or row.get("source") or "").strip()


def _manifestation(row: dict[str, Any]) -> dict[str, str]:
    """Keep only observed retrieval metadata; never infer missing provenance."""

    manifestation = {
        "provider": _provider_name(row),
        "source": str(row.get("source") or "").strip(),
        "doi": normalize_doi(row.get("doi") or row.get("doi_normalized")),
        "pmid": normalize_pmid(row.get("pmid") or row.get("pmid_normalized")),
        "pmcid": normalize_pmcid(row.get("pmcid")),
        "url": normalize_url(row.get("url") or row.get("url_normalized")),
        "provider_query": str(row.get("provider_query") or row.get("query") or "").strip(),
        "query_dialect": str(row.get("query_dialect") or "").strip(),
        "retrieved_at": str(
            row.get("interactive_retrieved_at") or row.get("retrieved_at") or ""
        ).strip(),
    }
    return {key: value for key, value in manifestation.items() if value}


def _manifestation_key(item: dict[str, str]) -> tuple[str, ...]:
    return tuple(
        item.get(key, "")
        for key in (
            "provider",
            "source",
            "doi",
            "pmid",
            "pmcid",
            "url",
            "provider_query",
            "query_dialect",
            "retrieved_at",
        )
    )


def _observed_provenance(*rows: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    providers: set[str] = set()
    manifestations: dict[tuple[str, ...], dict[str, str]] = {}

    for row in rows:
        existing_providers = row.get("source_providers")
        if isinstance(existing_providers, list):
            providers.update(str(value).strip() for value in existing_providers if str(value).strip())

        existing_manifestations = row.get("source_manifestations")
        if isinstance(existing_manifestations, list):
            for value in existing_manifestations:
                if not isinstance(value, dict):
                    continue
                normalized = _manifestation(value)
                if normalized:
                    if normalized.get("provider"):
                        providers.add(normalized["provider"])
                    manifestations[_manifestation_key(normalized)] = normalized

        own = _manifestation(row)
        if own:
            if own.get("provider"):
                providers.add(own["provider"])
            manifestations[_manifestation_key(own)] = own

    ordered_providers = sorted(providers, key=str.casefold)
    ordered_manifestations = sorted(
        manifestations.values(),
        key=lambda item: (
            item.get("provider", "").casefold(),
            item.get("doi", ""),
            item.get("pmid", ""),
            item.get("url", ""),
            item.get("provider_query", ""),
        ),
    )
    return ordered_providers, ordered_manifestations


def _with_provenance(record: dict[str, Any], *observed_rows: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(record)
    providers, manifestations = _observed_provenance(record, *observed_rows)
    if providers:
        enriched["source_providers"] = providers
    if manifestations:
        enriched["source_manifestations"] = manifestations
    return enriched


def _observed_strong_identifiers(row: dict[str, Any]) -> dict[str, set[str]]:
    values: dict[str, set[str]] = {"doi": set(), "pmid": set(), "pmcid": set()}

    def add_from(value: dict[str, Any]) -> None:
        doi = normalize_doi(value.get("doi") or value.get("doi_normalized"))
        pmid = normalize_pmid(value.get("pmid") or value.get("pmid_normalized"))
        pmcid = normalize_pmcid(value.get("pmcid"))
        if doi:
            values["doi"].add(doi)
        if pmid:
            values["pmid"].add(pmid)
        if pmcid:
            values["pmcid"].add(pmcid)

    add_from(row)
    manifestations = row.get("source_manifestations")
    if isinstance(manifestations, list):
        for manifestation in manifestations:
            if isinstance(manifestation, dict):
                add_from(manifestation)
    return values


def _strong_identity_conflict(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Fail closed when both sides assert incompatible strong identifiers of the same kind."""

    left_ids = _observed_strong_identifiers(left)
    right_ids = _observed_strong_identifiers(right)
    for kind in ("doi", "pmid", "pmcid"):
        if left_ids[kind] and right_ids[kind] and left_ids[kind].isdisjoint(right_ids[kind]):
            return True
    return False


def _merge_descriptive(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_text = str(left.get("abstract") or left.get("summary") or left.get("snippet") or "")
    right_text = str(right.get("abstract") or right.get("summary") or right.get("snippet") or "")
    winner = right if len(right_text) > len(left_text) else left
    return _with_provenance(dict(winner), left, right)


def _fresh_group_key(base: str, groups: dict[str, dict[str, Any]]) -> str:
    if base not in groups:
        return base
    index = 2
    while f"{base}#conflict-{index}" in groups:
        index += 1
    return f"{base}#conflict-{index}"


def dedupe_records(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate by exact observed aliases while preserving provider manifestations.

    A row may bridge DOI/PMID/PMCID/URL manifestations when an exact alias overlaps. Any conflict
    between strong identifiers keeps records separate. Exact-title fallback remains limited to rows
    without exact identifiers/URLs. Provider multiplicity is provenance only and adds no rank weight.
    """

    groups: dict[str, dict[str, Any]] = {}
    alias_to_group: dict[str, str] = {}
    unkeyed: list[dict[str, Any]] = []

    for raw_row in rows:
        row = dict(raw_row)
        aliases = _exact_identity_aliases(row)
        canonical = canonical_identity(row)
        if not aliases or not canonical:
            unkeyed.append(_with_provenance(row))
            continue

        candidates: list[str] = []
        for alias in aliases:
            group_key = alias_to_group.get(alias)
            if not group_key or group_key in candidates:
                continue
            current = groups.get(group_key)
            if current is not None and not _strong_identity_conflict(current, row):
                candidates.append(group_key)

        ambiguous = any(
            _strong_identity_conflict(groups[left], groups[right])
            for left, right in combinations(candidates, 2)
        )
        if ambiguous:
            candidates = []

        if not candidates:
            group_key = _fresh_group_key(canonical, groups)
            groups[group_key] = _with_provenance(row)
            for alias in aliases:
                alias_to_group.setdefault(alias, group_key)
            continue

        target = candidates[0]
        merged = groups[target]
        for other in candidates[1:]:
            merged = _merge_descriptive(merged, groups[other])
            del groups[other]
            for alias, mapped in list(alias_to_group.items()):
                if mapped == other:
                    alias_to_group[alias] = target

        merged = _merge_descriptive(merged, row)
        groups[target] = merged
        for alias in aliases:
            mapped = alias_to_group.get(alias)
            if mapped is None or mapped in candidates:
                alias_to_group[alias] = target

    return list(groups.values()) + unkeyed
