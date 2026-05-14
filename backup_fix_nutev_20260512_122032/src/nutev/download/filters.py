from __future__ import annotations
PRIORITY_EXT = {"pdf", "docx", "xlsx", "csv", "txt", "doc", "xls"}
BLOCKED_TOKENS = {"login","signin","search","tag","newsletter","careers","donate","privacy","contact","category","archive"}
RELEVANT_HTML = {"guideline","statement","report","consensus","official","recommendation"}

def is_likely_relevant_url(url: str) -> bool:
    return not any(tok in url.lower() for tok in BLOCKED_TOKENS)

def should_download(url: str, ext: str) -> bool:
    if not is_likely_relevant_url(url):
        return False
    e = ext.lower().lstrip(".")
    if e in PRIORITY_EXT:
        return True
    if e in {"html","htm"}:
        u = url.lower()
        return any(k in u for k in RELEVANT_HTML)
    return False
