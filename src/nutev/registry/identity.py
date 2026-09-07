from __future__ import annotations

from hashlib import sha256
from typing import Any, Iterable

from nutev.reference_identity import (
    normalize_doi,
    normalize_pmcid,
    normalize_pmid,
    normalize_title,
    normalize_url,
)

from .models import RegistryAlias

STRONG_ALIAS_SCHEMES = ("doi", "pmid", "pmcid")


def _provider_name(record: dict[str, Any], fallback: str = "") -> str:
    return str(
        record.get("source_provider")
        or record.get("provider")
        or record.get("source")
        or fallback
        or ""
    ).strip()


def _plain(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _provider_identifier(value: Any, *, prefix: str = "") -> str:
    text = _plain(value).casefold()
    if prefix and text.startswith(prefix.casefold()):
        text = text[len(prefix) :].strip(" /:")
    return text


def metadata_fingerprint(record: dict[str, Any]) -> str:
    """Conservative exact-metadata fallback used only without observed aliases."""

    title = normalize_title(record.get("title"))
    if not title:
        return ""
    year = _plain(record.get("year") or record.get("publication_year"))
    journal = normalize_title(record.get("journal") or record.get("venue"))
    payload = f"{title}|{year}|{journal}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _aliases_from_record(record: dict[str, Any], *, provider: str = "") -> list[RegistryAlias]:
    provider = _provider_name(record, provider)
    aliases: list[RegistryAlias] = []

    def add(scheme: str, normalized: str, raw: Any) -> None:
        if normalized:
            aliases.append(
                RegistryAlias(
                    scheme=scheme,
                    normalized_value=normalized,
                    raw_value=_plain(raw),
                    provider=provider,
                )
            )

    raw_doi = record.get("doi") or record.get("doi_normalized")
    raw_pmid = record.get("pmid") or record.get("pmid_normalized")
    raw_pmcid = record.get("pmcid") or record.get("pmc_id")
    raw_url = record.get("url") or record.get("url_normalized") or record.get("landing_page_url")
    add("doi", normalize_doi(raw_doi), raw_doi)
    add("pmid", normalize_pmid(raw_pmid), raw_pmid)
    pmcid = normalize_pmcid(raw_pmcid)
    add("pmcid", pmcid.casefold() if pmcid else "", raw_pmcid)
    add("url", normalize_url(raw_url).casefold(), raw_url)

    raw_openalex = record.get("openalex_id") or record.get("openalex")
    openalex = _provider_identifier(raw_openalex, prefix="https://openalex.org/")
    add("openalex", openalex, raw_openalex)

    raw_semantic = (
        record.get("semantic_scholar_id")
        or record.get("semantic_scholar_paper_id")
        or record.get("paper_id")
    )
    semantic = _provider_identifier(raw_semantic)
    add("semantic_scholar", semantic, raw_semantic)

    raw_crossref = record.get("crossref_id")
    crossref = _provider_identifier(raw_crossref)
    add("crossref", crossref, raw_crossref)
    return aliases


def observed_aliases(record: dict[str, Any], *, provider: str = "") -> tuple[RegistryAlias, ...]:
    """Return exact observed aliases without fuzzy repair or title inference."""

    aliases = _aliases_from_record(record, provider=provider)
    manifestations = record.get("source_manifestations")
    if isinstance(manifestations, list):
        for manifestation in manifestations:
            if isinstance(manifestation, dict):
                aliases.extend(
                    _aliases_from_record(
                        manifestation,
                        provider=_provider_name(manifestation, provider),
                    )
                )

    unique: dict[tuple[str, str], RegistryAlias] = {}
    for alias in aliases:
        unique.setdefault((alias.scheme, alias.normalized_value), alias)

    if not unique:
        fingerprint = metadata_fingerprint(record)
        if fingerprint:
            unique[("metadata_fingerprint", fingerprint)] = RegistryAlias(
                scheme="metadata_fingerprint",
                normalized_value=fingerprint,
                raw_value=normalize_title(record.get("title")),
                provider=_provider_name(record, provider),
            )
    return tuple(unique.values())


def alias_keys(aliases: Iterable[RegistryAlias]) -> tuple[tuple[str, str], ...]:
    return tuple((alias.scheme, alias.normalized_value) for alias in aliases)


def strong_identifier_sets(
    aliases: Iterable[RegistryAlias],
) -> dict[str, set[str]]:
    values = {scheme: set() for scheme in STRONG_ALIAS_SCHEMES}
    for alias in aliases:
        if alias.scheme in values:
            values[alias.scheme].add(alias.normalized_value)
    return values


def has_strong_conflict(
    existing_aliases: Iterable[RegistryAlias],
    incoming_aliases: Iterable[RegistryAlias],
) -> bool:
    """Fail closed when both sides assert incompatible strong IDs of one kind."""

    existing = strong_identifier_sets(existing_aliases)
    incoming = strong_identifier_sets(incoming_aliases)
    for scheme in STRONG_ALIAS_SCHEMES:
        if existing[scheme] and incoming[scheme] and existing[scheme].isdisjoint(incoming[scheme]):
            return True
    return False
