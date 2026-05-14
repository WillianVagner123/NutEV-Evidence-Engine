from __future__ import annotations
from urllib.parse import urlparse

PRIORITY_EXT = {"pdf", "docx", "xlsx", "csv", "txt", "doc", "xls"}

BLOCKED_TOKENS = {
    "javascript:void",
    "mostdownload.php",
    "/tdm/v1/articles/",
    "content.aspx?aid=",
    "book/chapter-pdf",
    "/lookup/doi/",
    "newsletter",
    "careers",
    "donate",
    "privacy",
    "contact",
    "category",
    "archive",
    "buy/pe",
}

BLOCKED_HOST_HINTS = {
    "psychiatryonline.org",
    "psycnet.apa.org",
}

RELEVANT_HTML = {
    "guideline", "guidelines", "statement", "report", "consensus",
    "official", "recommendation", "recommendations",
    "nutrition", "diet", "obesity", "lifestyle",
    "framework", "questionnaire", "food", "commensality",
    "adherence", "trial", "review", "journal", "article"
}

SCHOLARLY_HOST_HINTS = {
    "springer.com", "nature.com", "cambridge.org", "frontiersin.org",
    "karger.com", "oup.com", "scielo.br", "ahajournals.org",
    "cureus.com", "dovepress.com", "ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov", "bmj.com", "gastrojournal.org",
    "diabetesjournals.org", "biomedcentral.com", "taylorfrancis.com"
}

OFFICIAL_HOST_HINTS = {
    "who.int", "heart.org", "diabetesjournals.org", "lifestylemedicine.org",
    "gov", "nih.gov", "paho.org", "fao.org", "scielo.br",
    "abccardiol.org", "unicef.org"
}


def _host_has_any(url: str, hints: set[str]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(hint in host for hint in hints)


def is_likely_relevant_url(url: str) -> bool:
    u = (url or "").lower()
    if not u.startswith(("http://", "https://")):
        return False
    if any(tok in u for tok in BLOCKED_TOKENS):
        return False
    if _host_has_any(url, BLOCKED_HOST_HINTS):
        return False
    return True


def should_download(url: str, ext: str, source: str | None = None) -> bool:
    if not is_likely_relevant_url(url):
        return False

    e = ext.lower().lstrip(".")

    if e in PRIORITY_EXT:
        return True

    if source == "official" and e in {"html", "htm"}:
        return True

    if _host_has_any(url, OFFICIAL_HOST_HINTS) and e in {"html", "htm"}:
        return True

    if _host_has_any(url, SCHOLARLY_HOST_HINTS) and e in {"html", "htm"}:
        path = urlparse(url).path.lower()
        if any(tok in path for tok in ["/article", "/articles", "/doi", "/content", "/journal", "/journals", "/full", "/abstract"]):
            return True

    if e in {"html", "htm"}:
        u = url.lower()
        return any(k in u for k in RELEVANT_HTML)

    return False