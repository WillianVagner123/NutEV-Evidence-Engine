from __future__ import annotations

from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "NutEV Research Pipeline/1.0"
}


def _safe_get(url: str, timeout: int = 20) -> requests.Response | None:
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True, headers=HEADERS)
        r.raise_for_status()
        return r
    except Exception:
        return None


def _safe_head(url: str, timeout: int = 10) -> requests.Response | None:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers=HEADERS)
        return r
    except Exception:
        return None


def _extract_pdf_like_link(base_url: str, html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        href_l = href.lower()
        text_l = a.get_text(" ", strip=True).lower()

        if ".pdf" in href_l or "pdf" in text_l or "full text" in text_l or "download" in text_l:
            return requests.compat.urljoin(base_url, href)

    return None


def _resolve_doi(url: str) -> tuple[str, str]:
    r = _safe_get(url)
    if not r:
        return url, "unknown"

    final_url = r.url
    ctype = r.headers.get("Content-Type", "").lower()

    if "pdf" in ctype or final_url.lower().endswith(".pdf"):
        return final_url, "pdf"

    pdf_link = _extract_pdf_like_link(final_url, r.text)
    if pdf_link:
        return pdf_link, "pdf"

    return final_url, "html"


def _resolve_pubmed(url: str) -> tuple[str, str]:
    r = _safe_get(url)
    if not r:
        return url, "unknown"

    final_url = r.url
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        href_l = href.lower()
        if "pmc" in href_l or "full text" in a.get_text(" ", strip=True).lower():
            target = requests.compat.urljoin(final_url, href)
            return target, "html"

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "doi.org" in href.lower():
            return _resolve_doi(requests.compat.urljoin(final_url, href))

    return final_url, "html"


def _resolve_openalex(url: str) -> tuple[str, str]:
    return url, "html"


def _resolve_generic(url: str) -> tuple[str, str]:
    h = _safe_head(url)
    if h is not None:
        ctype = h.headers.get("Content-Type", "").lower()
        if "pdf" in ctype:
            return str(h.url), "pdf"
        if "html" in ctype:
            return str(h.url), "html"

    r = _safe_get(url)
    if not r:
        return url, "unknown"

    ctype = r.headers.get("Content-Type", "").lower()
    final_url = r.url

    if "pdf" in ctype or final_url.lower().endswith(".pdf"):
        return final_url, "pdf"

    pdf_link = _extract_pdf_like_link(final_url, r.text)
    if pdf_link:
        return pdf_link, "pdf"

    return final_url, "html"


def resolve_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "doi.org" in host:
        return _resolve_doi(url)

    if "pubmed.ncbi.nlm.nih.gov" in host:
        return _resolve_pubmed(url)

    if "openalex.org" in host:
        return _resolve_openalex(url)

    return _resolve_generic(url)