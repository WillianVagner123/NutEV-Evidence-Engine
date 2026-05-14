from __future__ import annotations
import requests


def search_pubmed(query: str, retmax: int = 5) -> list[dict]:
    esearch = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params={"db": "pubmed", "retmode": "json", "term": query, "retmax": retmax}, timeout=30)
    esearch.raise_for_status()
    ids = esearch.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    summary = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)}, timeout=30)
    summary.raise_for_status()
    payload = summary.json().get("result", {})
    out = []
    for pmid in ids:
        item = payload.get(pmid, {})
        out.append({"source": "pubmed", "title": item.get("title"), "doi": item.get("elocationid"), "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
    return out
