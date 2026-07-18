"""Live discovery of FAO Food-Based Dietary Guidelines (FBDG) by country.

The static country manifest (``config/official_sources_countries.json``) is a
fixed seed list. This module instead crawls the FAO FBDG registry *live* to find
**every** country page and the **actual downloadable guide files** on each — the
real "pegar todos os guias". For each country it reads the official name and
publication year and returns one guide *source* per downloadable file (or the
country page itself when no file is listed), in the exact shape
:func:`nutev.acquire.guias_fetcher.fetch_guide` consumes.

The HTTP session is injected (mockable, rate-limitable); nothing here bypasses a
paywall or fabricates data — FAO FBDG pages are public. Parsing is best-effort
and defensive: a country that fails to parse is skipped, never fatal.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

FAO_HOME = "https://www.fao.org/nutrition/education/food-dietary-guidelines"
_COUNTRY_HREF = "/nutrition/education/food-dietary-guidelines/regions/countries/"
_FILE_EXTS = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx")


def _get(session: Any, url: str, timeout: float) -> str:
    """Return response text for ``url`` or '' on any non-200 / error."""
    try:
        resp = session.get(url, timeout=timeout)
    except Exception:
        return ""
    if getattr(resp, "status_code", 200) != 200:
        return ""
    return getattr(resp, "text", "") or ""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def collect_country_urls(home_html: str, home_url: str = FAO_HOME) -> list[str]:
    """Return the normalized (…/en/) country-page URLs linked from the home page."""
    soup = _soup(home_html)
    urls: set[str] = set()
    for a in soup.select(f'a[href*="{_COUNTRY_HREF}"]'):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        abs_url = urljoin(home_url, href)
        path = urlparse(abs_url).path
        if _COUNTRY_HREF not in path:
            continue
        if not path.endswith("/en/"):
            abs_url = abs_url + ("en/" if abs_url.endswith("/") else "/en/")
        urls.add(abs_url)
    return sorted(urls)


def _country_slug(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    try:
        return parts[parts.index("countries") + 1]
    except Exception:
        return parts[-2] if len(parts) >= 2 else "country"


def _field_value(soup: BeautifulSoup, label: str) -> str:
    """Read a labelled field (e.g. 'Official name', 'Publication year')."""
    node = soup.find(string=re.compile(rf"^{re.escape(label)}$", re.I))
    if not node:
        return ""
    parent = node.parent
    for _ in range(12):
        parent = parent.find_next() if parent else None
        if not parent:
            break
        txt = _norm(parent.get_text(" ", strip=True))
        if txt and txt.lower() != label.lower():
            return txt
    return ""


def _downloadables(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Return the 'Downloadable materials' file links on a country page."""
    heading = soup.find(string=re.compile(r"Downloadable materials", re.I))
    if not heading:
        return []
    container = heading.parent
    ul = container.find_next("ul") if container else None
    if not ul:
        return []
    out: list[dict] = []
    for li in ul.find_all("li"):
        a = li.find("a", href=True)
        if not a:
            continue
        out.append({
            "title": _norm(li.get_text(" ", strip=True)),
            "url": urljoin(base_url, a["href"].strip()),
        })
    return out


def _is_file_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(_FILE_EXTS)


def scrape_country(country_html: str, url: str) -> dict:
    """Parse one country page into its official name, year and downloadables."""
    soup = _soup(country_html)
    h1 = soup.find("h1")
    return {
        "country_url": url,
        "country_slug": _country_slug(url),
        "page_title": _norm(h1.get_text(" ", strip=True)) if h1 else "",
        "official_name": _field_value(soup, "Official name"),
        "publication_year": _field_value(soup, "Publication year"),
        "downloadables": _downloadables(soup, url),
    }


def country_to_sources(country: dict) -> list[dict]:
    """Turn a scraped country into guide *source* dicts for ``fetch_guide``.

    One source per downloadable file (preferred — that is the actual guide); if a
    country lists none, one source pointing at the country page (HTML) so it is
    still captured. Carries country/official name/year/institution provenance.
    """
    slug = country.get("country_slug", "")
    official = country.get("official_name") or country.get("page_title") or slug
    year = country.get("publication_year", "")
    files = [d for d in country.get("downloadables", []) if _is_file_url(d.get("url", ""))]
    base = {
        "country": slug,
        "institution": "FAO FBDG / national authority",
        "document_version": year,
        "source_page": country.get("country_url", ""),
    }
    if files:
        return [
            {**base, "name": d.get("title") or official, "url": d["url"], "title": official}
            for d in files
        ]
    return [{**base, "name": official, "url": country.get("country_url", ""), "title": official}]


def discover_fao_guides(
    session: Any,
    *,
    home_url: str = FAO_HOME,
    timeout: float = 60.0,
    limit: int | None = None,
    logger: Any | None = None,
) -> list[dict]:
    """Crawl the FAO FBDG registry and return guide sources for every country.

    Sources are compatible with :func:`guias_fetcher.fetch_guide`. The crawl is
    read-only and best-effort: a country that fails to fetch/parse is skipped.
    """
    home_html = _get(session, home_url, timeout)
    country_urls = collect_country_urls(home_html, home_url)
    if logger:
        logger.info("FAO FBDG: %d países descobertos", len(country_urls))
    if limit is not None:
        country_urls = country_urls[:limit]

    sources: list[dict] = []
    for i, url in enumerate(country_urls, start=1):
        html = _get(session, url, timeout)
        if not html:
            if logger:
                logger.warning("FAO FBDG: falha ao ler país %s", url)
            continue
        try:
            country = scrape_country(html, url)
            sources.extend(country_to_sources(country))
        except Exception as exc:  # defensive: skip a bad page, never abort
            if logger:
                logger.warning("FAO FBDG: erro no país %s: %s", url, exc)
        if logger and i % 25 == 0:
            logger.info("FAO FBDG: %d/%d países processados", i, len(country_urls))
    if logger:
        sources_with_file = sum(1 for s in sources if _is_file_url(s.get("url", "")))
        logger.info("FAO FBDG: %d fontes (%d arquivos diretos)", len(sources), sources_with_file)
    return sources
