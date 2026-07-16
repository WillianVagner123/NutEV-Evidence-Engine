"""Build a precise, citable reference for a source document.

Every extracted text and key phrase must be traceable to the *reference itself* —
not just the sentence. This module assembles a bibliographic citation string plus
the structured fields behind it, from the provenance already captured for each
guide/record (issuing body, title, country, version/year, URL, access date and
the SHA-256 of the archived file).

It never invents bibliographic data: only fields actually present are included,
and the SHA-256 anchors the exact file version (guidelines get re-issued and
links break). The output is for a human to cite; nothing here is authoritative on
its own.
"""
from __future__ import annotations


def _first(record: dict, *keys: str) -> str:
    for key in keys:
        value = str(record.get(key, "") or "").strip()
        if value:
            return value
    return ""


def reference_fields(record: dict) -> dict:
    """Return the structured reference fields for a record (all strings)."""
    return {
        "reference_institution": _first(record, "issuing_body", "institution", "source_institution"),
        "reference_title": _first(record, "title", "name"),
        "reference_country": _first(record, "country"),
        "reference_version": _first(record, "document_version", "year"),
        "reference_url": _first(record, "official_url", "source_url", "final_url", "url"),
        "reference_access_date": _first(record, "access_date"),
        "reference_sha256": _first(record, "archived_pdf_sha256", "sha256"),
    }


def format_reference(record: dict) -> str:
    """Assemble a single-line citation string from the reference fields.

    Shape: ``Institution. Title. Country. Version/Year. Disponível em: URL.
    Acesso em: DATE. SHA-256: HASH.`` — only the parts that exist are emitted.
    """
    f = reference_fields(record)
    parts: list[str] = []
    if f["reference_institution"]:
        parts.append(f["reference_institution"])
    if f["reference_title"]:
        parts.append(f["reference_title"])
    if f["reference_country"]:
        parts.append(f["reference_country"])
    if f["reference_version"]:
        parts.append(f["reference_version"])
    citation = ". ".join(parts)
    if citation and not citation.endswith("."):
        citation += "."
    if f["reference_url"]:
        citation += f" Disponível em: {f['reference_url']}."
    if f["reference_access_date"]:
        citation += f" Acesso em: {f['reference_access_date']}."
    if f["reference_sha256"]:
        citation += f" SHA-256: {f['reference_sha256']}."
    return citation.strip()


def build_reference(record: dict) -> dict:
    """Return both the formatted citation and its structured fields."""
    fields = reference_fields(record)
    fields["reference"] = format_reference(record)
    return fields
