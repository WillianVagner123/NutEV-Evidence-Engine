from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import uuid

from nutev.engine.validators import canonical_document_key


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def make_run_id() -> str:
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def make_case_id() -> str:
    return f"case_{uuid.uuid4().hex[:10]}"


def make_job_id() -> str:
    return f"job_{uuid.uuid4().hex[:10]}"


def make_document_id(candidate: dict) -> str:
    return f"doc_{_short_hash(canonical_document_key(candidate))}"
