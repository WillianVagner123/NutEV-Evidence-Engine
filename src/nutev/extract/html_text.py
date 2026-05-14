from __future__ import annotations
from bs4 import BeautifulSoup

def extract_html_text(content: str) -> dict:
    soup = BeautifulSoup(content, "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1","h2","h3"])][:50]
    body = "\n".join(p.get_text(" ", strip=True) for p in soup.find_all(["p","li"]))
    return {"title": title, "headings": headings, "body": body.strip()}
