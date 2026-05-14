from __future__ import annotations
import hashlib, re
from pathlib import Path
from urllib.parse import urlparse

def safe_slug(text: str, max_len: int = 10) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "doc").lower()).strip("-")
    return (slug or "doc")[:max_len]

def hash6(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:6]

def infer_ext(url: str, content_type: str | None = None) -> str:
    path = urlparse(url).path.lower()
    if "." in Path(path).name:
        return Path(path).suffix.lstrip(".") or "bin"
    ct = (content_type or "").lower()
    mapping = {"application/pdf":"pdf","application/vnd.openxmlformats-officedocument.wordprocessingml.document":"docx","application/msword":"doc","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":"xlsx","application/vnd.ms-excel":"xls","text/csv":"csv","text/plain":"txt","text/html":"html"}
    for k,v in mapping.items():
        if k in ct:
            return v
    return "bin"

def build_filename(workstream: str, source: str, title: str, url: str, ext: str) -> str:
    return f"NTV__{workstream}__{safe_slug(source,6)}__{safe_slug(title,10)}__{hash6(url)}.{ext}"
