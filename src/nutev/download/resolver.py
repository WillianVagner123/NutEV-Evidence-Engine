from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

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
PDF_LINK_HINTS = [
    ".pdf",
    "/pdf",
    "pdfdirect",
    "format=pdf",
    "article-pdf",
    "article/download",
    "/download/",
    ".full.pdf",
    # Additional publisher-platform patterns for broader full-text capture.
    "/doi/pdf",
    "/doi/epdf",
    "/content/pdf",
    "epdf",
    "getpdf",
    "pdfft",          # Elsevier ScienceDirect
    "type=printable",
    "/pdf/",
    "downloadpdf",
    "render=pdf",
    "viewpdf",
]
PDF_TEXT_HINTS = [
    "pdf",
    "download pdf",
    "article pdf",
    "full text pdf",
    "baixar pdf",
    "texto completo",
]
PDF_META_NAMES = [
    "citation_pdf_url",
    "dc.identifier",
    "eprints.document_url",
    "bepress_citation_pdf_url",
]


def extract_clean_doi(value: str | None) -> str | None:
    if not value:
        return None
    raw = unquote(str(value)).strip()
    raw = raw.replace("doi:", " ").replace("DOI:", " ")
    match = DOI_RE.search(raw)
    if not match:
        return None
    return match.group(1).rstrip(" .;,)")


def normalize_candidate_url(url: str) -> str:
    raw = unquote((url or "").strip())
    if not raw:
        return raw

    doi = extract_clean_doi(raw)
    if doi and (
        "doi.org" in raw or raw.startswith("10.") or "pii:" in raw.lower()
    ):
        return f"https://doi.org/{doi}"

    return raw


def _looks_pdfish(url: str) -> bool:
    normalized_url = (url or "").lower()
    return any(token in normalized_url for token in PDF_LINK_HINTS)


def _safe_get(url: str, timeout: int = 25) -> requests.Response | None:
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=HEADERS,
        )
        response.raise_for_status()
        return response
    except Exception:
        return None


def _safe_head(url: str, timeout: int = 15) -> requests.Response | None:
    try:
        return requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=HEADERS,
        )
    except Exception:
        return None


def _join(base_url: str, href: str) -> str:
    return requests.compat.urljoin(base_url, href.strip())


def _is_candidate_pdf_href(href: str, text: str = "") -> bool:
    href_lower = (href or "").lower()
    text_lower = (text or "").lower()
    return any(token in href_lower for token in PDF_LINK_HINTS) or any(
        token in text_lower for token in PDF_TEXT_HINTS
    )


def _extract_pdf_from_meta(base_url: str, soup: BeautifulSoup) -> str | None:
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").strip().lower()
        content = (meta.get("content") or "").strip()
        if not content:
            continue
        if name in PDF_META_NAMES or _looks_pdfish(content):
            return _join(base_url, content)
    return None


def _extract_pdf_from_link_tags(base_url: str, soup: BeautifulSoup) -> str | None:
    for link in soup.find_all("link", href=True):
        href = (link.get("href") or "").strip()
        rel = " ".join(link.get("rel") or []).lower()
        link_type = (link.get("type") or "").lower()
        if not href:
            continue
        if "pdf" in link_type or "alternate" in rel or _looks_pdfish(href):
            if _is_candidate_pdf_href(href, link_type):
                return _join(base_url, href)
    return None


def _extract_pdf_from_anchors(base_url: str, soup: BeautifulSoup) -> str | None:
    for link in soup.find_all("a", href=True):
        href = (link["href"] or "").strip()
        if not href or href.lower().startswith(("javascript:", "mailto:", "#")):
            continue
        text = link.get_text(" ", strip=True)
        aria = link.get("aria-label") or ""
        title = link.get("title") or ""
        if _is_candidate_pdf_href(href, f"{text} {aria} {title}"):
            return _join(base_url, href)
    return None


def _extract_pdf_from_meta_refresh(base_url: str, soup: BeautifulSoup) -> str | None:
    for meta in soup.find_all("meta"):
        equiv = (meta.get("http-equiv") or "").strip().lower()
        if equiv != "refresh":
            continue
        content = (meta.get("content") or "")
        marker = content.lower().find("url=")
        if marker == -1:
            continue
        target = content[marker + 4:].strip().strip("'\"")
        if target and _looks_pdfish(target):
            return _join(base_url, target)
    return None


def _extract_pdf_like_link(base_url: str, html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    return (
        _extract_pdf_from_meta(base_url, soup)
        or _extract_pdf_from_meta_refresh(base_url, soup)
        or _extract_pdf_from_link_tags(base_url, soup)
        or _extract_pdf_from_anchors(base_url, soup)
    )


def _resolve_doi(url: str) -> tuple[str, str]:
    normalized_url = normalize_candidate_url(url)
    response = _safe_get(normalized_url)
    if not response:
        return normalized_url, "unknown"

    final_url = response.url
    content_type = response.headers.get("Content-Type", "").lower()

    if "pdf" in content_type or _looks_pdfish(final_url):
        return final_url, "pdf"

    pdf_link = _extract_pdf_like_link(final_url, response.text)
    if pdf_link:
        return pdf_link, "pdf"

    return final_url, "html"


def _resolve_pubmed(url: str) -> tuple[str, str]:
    response = _safe_get(url)
    if not response:
        return url, "unknown"

    final_url = response.url
    soup = BeautifulSoup(response.text, "html.parser")

    pdf_link = _extract_pdf_like_link(final_url, response.text)
    if pdf_link:
        return pdf_link, "pdf"

    for link in soup.find_all("a", href=True):
        href = (link["href"] or "").strip()
        href_lower = href.lower()
        text_lower = link.get_text(" ", strip=True).lower()

        if "/pmc/articles/" in href_lower:
            pmc_url = requests.compat.urljoin(final_url, href)
            return _resolve_generic(pmc_url)

        if "pmc" in href_lower or "full text" in text_lower:
            target = requests.compat.urljoin(final_url, href)
            return _resolve_generic(target)

    for link in soup.find_all("a", href=True):
        href = (link["href"] or "").strip()
        if "doi.org" in href.lower():
            target = requests.compat.urljoin(final_url, href)
            return _resolve_doi(target)

    return final_url, "html"


def _resolve_openalex(url: str) -> tuple[str, str]:
    if _looks_pdfish(url):
        return url, "pdf"
    return _resolve_generic(url)


def _resolve_generic(url: str) -> tuple[str, str]:
    normalized_url = normalize_candidate_url(url)
    if not normalized_url or normalized_url.lower().startswith(
        ("javascript:", "mailto:", "#")
    ):
        return normalized_url, "unknown"

    parsed = urlparse(normalized_url)
    if (
        parsed.netloc.lower() == "pmc.ncbi.nlm.nih.gov"
        and parsed.path.strip("/") == ""
    ):
        return normalized_url, "unknown"

    if _looks_pdfish(normalized_url):
        return normalized_url, "pdf"

    head_response = _safe_head(normalized_url)
    if head_response is not None:
        content_type = head_response.headers.get("Content-Type", "").lower()
        if "pdf" in content_type:
            return str(head_response.url), "pdf"
        if "html" in content_type:
            if _looks_pdfish(str(head_response.url)):
                return str(head_response.url), "pdf"
            response = _safe_get(str(head_response.url))
            if response:
                pdf_link = _extract_pdf_like_link(response.url, response.text)
                if pdf_link:
                    return pdf_link, "pdf"
            return str(head_response.url), "html"

    response = _safe_get(normalized_url)
    if not response:
        return normalized_url, "unknown"

    content_type = response.headers.get("Content-Type", "").lower()
    final_url = response.url

    if "pdf" in content_type or _looks_pdfish(final_url):
        return final_url, "pdf"

    pdf_link = _extract_pdf_like_link(final_url, response.text)
    if pdf_link:
        return pdf_link, "pdf"

    return final_url, "html"


def resolve_url(url: str) -> tuple[str, str]:
    normalized_url = normalize_candidate_url(url)
    parsed = urlparse(normalized_url)
    host = parsed.netloc.lower()

    if "doi.org" in host or extract_clean_doi(normalized_url):
        return _resolve_doi(normalized_url)
    if "pubmed.ncbi.nlm.nih.gov" in host:
        return _resolve_pubmed(normalized_url)
    if "openalex.org" in host:
        return _resolve_openalex(normalized_url)

    return _resolve_generic(normalized_url)
