from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import uuid
from urllib.parse import urlparse, urlunparse

from nutev.engine.validators import normalize_doi


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def make_run_id() -> str:
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def make_case_id() -> str:
    return f"case_{uuid.uuid4().hex[:10]}"


def make_job_id() -> str:
    return f"job_{uuid.uuid4().hex[:10]}"


def _normalize_url(url: str) -> str:
    p = urlparse((url or "").strip())
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", p.query, ""))


def make_document_id(candidate: dict) -> str:
    doi = normalize_doi(candidate.get("doi"))
    if doi:
        return f"doc_{_short_hash('doi:' + doi)}"
    final_url = candidate.get("final_url") or candidate.get("url") or candidate.get("original_url")
    if final_url:
        return f"doc_{_short_hash('url:' + _normalize_url(str(final_url)))}"
    title = (candidate.get("title") or "").strip().lower()
    provider = (candidate.get("source_provider") or candidate.get("provider") or "").strip().lower()
    year = str(candidate.get("year") or "")
    return f"doc_{_short_hash('|'.join([title, provider, year]))}"
