from __future__ import annotations
from urllib.parse import urlparse

PRIORITY_EXT = {"pdf", "docx", "xlsx", "csv", "txt", "doc", "xls"}

BLOCKED_TOKENS = {
    "login", "signin", "search", "tag", "newsletter", "careers",
    "donate", "privacy", "contact", "category", "archive",
    "mostdownload", "top_down"
}

RELEVANT_HTML = {
    "guideline", "guidelines", "statement", "report", "consensus",
    "official", "recommendation", "recommendations",
    "healthy-diet", "standards", "nutrition", "diet",
    "obesity", "lifestyle", "competencies", "medical", "care",
    "framework", "questionnaire", "food", "commensality", "adherence"
}

OFFICIAL_HOST_HINTS = {
    "who.int",
    "heart.org",
    "diabetesjournals.org",
    "lifestylemedicine.org",
    "gov",
    "nih.gov",
    "paho.org",
    "fao.org",
    "scielo.br",
}


def is_likely_relevant_url(url: str) -> bool:
    u = url.lower()
    return not any(tok in u for tok in BLOCKED_TOKENS)


def _is_official_like_host(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(hint in host for hint in OFFICIAL_HOST_HINTS)


def should_download(url: str, ext: str, source: str | None = None) -> bool:
    if not is_likely_relevant_url(url):
        return False

    e = ext.lower().lstrip(".")

    if e in PRIORITY_EXT:
        return True

    if source == "official" and e in {"html", "htm"}:
        return True

    if _is_official_like_host(url) and e in {"html", "htm"}:
        return True

    if e in {"html", "htm"}:
        u = url.lower()
        return any(k in u for k in RELEVANT_HTML)

    return False