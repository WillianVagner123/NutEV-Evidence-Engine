from __future__ import annotations

import re
from bs4 import BeautifulSoup

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


def extract_clean_html_text(html: str) -> dict:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    title = (soup.title.get_text(" ", strip=True) if soup.title else "")
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(" ", strip=True)]

    abstract = ""
    keywords = ["abstract", "resumo", "summary", "background"]
    for el in soup.find_all(["section", "div", "p"]):
        txt = el.get_text(" ", strip=True)
        if any(k in txt.lower()[:80] for k in keywords) and len(txt) > 40:
            abstract = txt[:3000]
            break

    pdf_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if any(tok in href for tok in [".pdf", "/pdf", "pdfdirect", "download"]):
            pdf_links.append(a["href"])

    text = soup.get_text("\n", strip=True)
    doi_candidates = list(dict.fromkeys(DOI_RE.findall(text)))
    clean_text = text[:200000]

    return {
        "title": title,
        "abstract": abstract,
        "headings": headings[:100],
        "clean_text": clean_text,
        "doi_candidates": doi_candidates[:20],
        "pdf_links_found": pdf_links[:100],
    }
