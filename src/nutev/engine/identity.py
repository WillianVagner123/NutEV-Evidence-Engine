from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return "; ".join(as_text(v) for v in value if as_text(v))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def normalize_for_match(value: object) -> str:
    text = unicodedata.normalize("NFKD", as_text(value).lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return _WHITESPACE_RE.sub(" ", text).strip()


def normalize_doi(value: object) -> str:
    text = as_text(value).lower()
    if not text:
        return ""
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip().strip("/")


def normalize_url(value: object) -> str:
    text = as_text(value)
    if not text:
        return ""
    parsed = urlsplit(text)
    if not parsed.scheme or not parsed.netloc:
        return text.rstrip("/").lower()
    path = parsed.path.rstrip("/") or "/"
    normalized = urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", "")
    )
    return normalized.rstrip("/")


def normalize_title(value: object) -> str:
    text = _WHITESPACE_RE.sub(" ", as_text(value).lower()).strip()
    return _NON_ALNUM_RE.sub(" ", text).strip()


def normalize_year(value: object) -> str:
    text = as_text(value)
    if not text:
        return ""
    try:
        return str(int(float(text)))
    except Exception:
        return ""


def _hash_fallback(row: dict) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]  # noqa: S324


def compute_document_key(row: dict) -> tuple[str, str]:
    doi = normalize_doi(row.get("doi"))
    if doi:
        return doi, "doi"

    pmid = as_text(row.get("pmid"))
    if pmid:
        return f"pmid:{pmid}", "pmid"

    pmcid = normalize_for_match(row.get("pmcid"))
    if pmcid:
        return f"pmcid:{pmcid}", "pmcid"

    url = normalize_url(
        row.get("final_url")
        or row.get("original_url")
        or row.get("resolved_url")
        or row.get("url")
    )
    if url:
        return url, "url"

    title = normalize_title(row.get("title"))
    year = normalize_year(row.get("year"))
    if title and year:
        return f"{title}::{year}", "title_year"

    return _hash_fallback(row), "row_hash"


def has_full_text(row: dict) -> bool:
    statuses = {
        as_text(row.get("download_status")).lower(),
        as_text(row.get("capture_status")).lower(),
        as_text(row.get("extraction_status")).lower(),
    }
    if "pdf" in statuses or "html_snapshot" in statuses or "ok" in statuses:
        return True
    return bool(as_text(row.get("file_path")) or as_text(row.get("text_path")))


def url_capture_priority(url: str) -> tuple[int, int, int]:
    lowered = as_text(url).lower()
    return (
        int("pmc.ncbi.nlm.nih.gov" in lowered),
        int(lowered.endswith(".pdf")),
        len(lowered),
    )


def merge_article_rows(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    for key, value in incoming.items():
        if value in (None, "", [], {}):
            continue
        current = merged.get(key)
        if current in (None, "", [], {}):
            merged[key] = value
            continue
        if key in {"abstract", "summary"} and len(as_text(value)) > len(
            as_text(current)
        ):
            merged[key] = value

    existing_url = as_text(merged.get("url"))
    incoming_url = as_text(incoming.get("url"))
    if incoming_url and url_capture_priority(incoming_url) > url_capture_priority(
        existing_url
    ):
        merged["url"] = incoming_url

    merged["source"] = merged.get("source") or incoming.get("source")
    return merged


def _manifest_value(row: dict, key: str) -> str:
    return as_text(row.get(key))


def deduplicate_document_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Deduplicate document rows and return an audit manifest.

    The first occurrence owns the stable document position, while later occurrences
    can still enrich the final merged row through ``merge_article_rows``. The
    manifest is intentionally row-oriented so a reviewer can see every raw
    occurrence, whether it won, and which document key absorbed it.
    """

    by_key: dict[tuple[str, str], dict] = {}
    order: list[tuple[str, str]] = []
    occurrences: dict[tuple[str, str], list[tuple[int, dict]]] = {}

    for input_index, row in enumerate(rows):
        document_key, key_type = compute_document_key(row)
        compound_key = (document_key, key_type)
        occurrences.setdefault(compound_key, []).append((input_index, row))

        if compound_key not in by_key:
            by_key[compound_key] = dict(row)
            order.append(compound_key)
            continue
        by_key[compound_key] = merge_article_rows(by_key[compound_key], row)

    manifest: list[dict] = []
    for compound_key in order:
        document_key, key_type = compound_key
        final_row = by_key[compound_key]
        group = occurrences[compound_key]
        winner_input_index = group[0][0]
        absorbed_count = max(len(group) - 1, 0)

        for occurrence_order, (input_index, row) in enumerate(group):
            is_winner = occurrence_order == 0
            role = "winner" if is_winner else "absorbed"
            manifest.append(
                {
                    "workstream": _manifest_value(row, "workstream"),
                    "document_key": document_key,
                    "document_key_type": key_type,
                    "dedup_rule": f"same_{key_type}",
                    "occurrence_role": role,
                    "input_index": input_index,
                    "winner_input_index": winner_input_index,
                    "absorbed_count": absorbed_count if is_winner else "",
                    "merge_reason": "first_occurrence"
                    if is_winner
                    else f"absorbed_by_same_{key_type}",
                    "winner_url_after_merge": _manifest_value(final_row, "url"),
                    "occurrence_url": _manifest_value(row, "url"),
                    "source": _manifest_value(row, "source"),
                    "source_provider": _manifest_value(row, "source_provider"),
                    "title": _manifest_value(row, "title"),
                    "doi": _manifest_value(row, "doi"),
                    "pmid": _manifest_value(row, "pmid"),
                    "pmcid": _manifest_value(row, "pmcid"),
                    "year": _manifest_value(row, "year"),
                }
            )

    return [by_key[key] for key in order], manifest
