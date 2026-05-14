from __future__ import annotations

from urllib.parse import urlparse, unquote
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
}

DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.I)


def extract_clean_doi(value: str | None) -> str | None:
    if not value:
        return None
    raw = unquote(str(value)).strip()
    raw = raw.replace("doi:", " ").replace("DOI:", " ")
    match = DOI_RE.search(raw)
    if not match:
        return None
    doi = match.group(1).rstrip(" .;,)")
    return doi


def normalize_candidate_url(url: str) -> str:
    raw = unquote((url or "").strip())
    if not raw:
        return raw

    doi = extract_clean_doi(raw)
    if doi and ("doi.org" in raw or raw.startswith("10.") or "pii:" in raw.lower()):
        return f"https://doi.org/{doi}"

    return raw


def _looks_pdfish(url: str) -> bool:
    u = (url or "").lower()
    pdfish_tokens = [
        ".pdf", "/pdf", "pdfdirect", "format=pdf", "article-pdf",
        "_reference.pdf", "article/download", "/download/", ".full.pdf"
    ]
    return any(tok in u for tok in pdfish_tokens)


def _safe_get(url: str, timeout: int = 25) -> requests.Response | None:
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True, headers=HEADERS)
        r.raise_for_status()
        return r
    except Exception:
        return None


def _safe_head(url: str, timeout: int = 15) -> requests.Response | None:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers=HEADERS)
        return r
    except Exception:
        return None


def _extract_pdf_like_link(base_url: str, html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = (a["href"] or "").strip()
        href_l = href.lower()
        text_l = a.get_text(" ", strip=True).lower()
        if not href or href_l.startswith(("javascript:", "mailto:", "#")):
            continue
        if (
            ".pdf" in href_l or "/pdf" in href_l or "pdfdirect" in href_l
            or "download" in href_l or "full text" in text_l or "pdf" in text_l
        ):
            return requests.compat.urljoin(base_url, href)
    return None


def _resolve_doi(url: str) -> tuple[str, str]:
    url = normalize_candidate_url(url)
    r = _safe_get(url)
    if not r:
        return url, "unknown"

    final_url = r.url
    ctype = r.headers.get("Content-Type", "").lower()

    if "pdf" in ctype or _looks_pdfish(final_url):
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
        href = (a["href"] or "").strip()
        href_l = href.lower()
        text_l = a.get_text(" ", strip=True).lower()

        if "/pmc/articles/" in href_l:
            pmc_url = requests.compat.urljoin(final_url, href)
            return _resolve_generic(pmc_url)

        if "pmc" in href_l or "full text" in text_l:
            target = requests.compat.urljoin(final_url, href)
            return _resolve_generic(target)

    for a in soup.find_all("a", href=True):
        href = (a["href"] or "").strip()
        if "doi.org" in href.lower():
            return _resolve_doi(requests.compat.urljoin(final_url, href))

    return final_url, "html"


def _resolve_openalex(url: str) -> tuple[str, str]:
    if _looks_pdfish(url):
        return url, "pdf"
    return _resolve_generic(url)


def _resolve_generic(url: str) -> tuple[str, str]:
    url = normalize_candidate_url(url)
    if not url or url.lower().startswith(("javascript:", "mailto:", "#")):
        return url, "unknown"

    parsed = urlparse(url)
    if parsed.netloc.lower() == "pmc.ncbi.nlm.nih.gov" and parsed.path.strip("/") == "":
        return url, "unknown"

    if _looks_pdfish(url):
        return url, "pdf"

    h = _safe_head(url)
    if h is not None:
        ctype = h.headers.get("Content-Type", "").lower()
        if "pdf" in ctype:
            return str(h.url), "pdf"
        if "html" in ctype:
            if _looks_pdfish(str(h.url)):
                return str(h.url), "pdf"
            return str(h.url), "html"

    r = _safe_get(url)
    if not r:
        return url, "unknown"

    ctype = r.headers.get("Content-Type", "").lower()
    final_url = r.url

    if "pdf" in ctype or _looks_pdfish(final_url):
        return final_url, "pdf"

    pdf_link = _extract_pdf_like_link(final_url, r.text)
    if pdf_link:
        return pdf_link, "pdf"

    return final_url, "html"


def resolve_url(url: str) -> tuple[str, str]:
    url = normalize_candidate_url(url)
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "doi.org" in host or extract_clean_doi(url):
        return _resolve_doi(url)
    if "pubmed.ncbi.nlm.nih.gov" in host:
        return _resolve_pubmed(url)
    if "openalex.org" in host:
        return _resolve_openalex(url)

    return _resolve_generic(url)