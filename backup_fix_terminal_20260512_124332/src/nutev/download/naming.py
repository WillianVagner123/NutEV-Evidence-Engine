from __future__ import annotations
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs


def safe_slug(text: str, max_len: int = 10) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "doc").lower()).strip("-")
    return (slug or "doc")[:max_len]


def hash6(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:6]


def _looks_pdfish(url: str) -> bool:
    u = (url or "").lower()
    if ".pdf" in u:
        return True
    pdfish_tokens = [
        "/pdf",
        "pdfdirect",
        "format=pdf",
        "article-pdf",
        "_reference.pdf",
        "article/download",
        "/download/",
    ]
    return any(tok in u for tok in pdfish_tokens)


def infer_ext(url: str, content_type: str | None = None) -> str:
    if _looks_pdfish(url):
        return "pdf"

    parsed = urlparse(url)
    path = parsed.path.lower()

    if "." in Path(path).name:
        return Path(path).suffix.lstrip(".") or "bin"

    query = parse_qs(parsed.query)
    fmt = "".join(query.get("format", [])).lower()
    if fmt == "pdf":
        return "pdf"

    ct = (content_type or "").lower()
    mapping = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "application/vnd.ms-excel": "xls",
        "text/csv": "csv",
        "text/plain": "txt",
        "text/html": "html",
    }
    for k, v in mapping.items():
        if k in ct:
            return v

    return "bin"


def build_filename(workstream: str, source: str, title: str, url: str, ext: str) -> str:
    return f"NTV__{workstream}__{safe_slug(source,6)}__{safe_slug(title,10)}__{hash6(url)}.{ext}"