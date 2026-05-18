from __future__ import annotations

from nutev.engine.identity import normalize_doi as _normalize_doi


def normalize_doi(doi: str | None) -> str | None:
    cleaned = _normalize_doi(doi)
    return cleaned or None
