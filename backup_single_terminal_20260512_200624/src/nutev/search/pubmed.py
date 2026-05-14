from __future__ import annotations
import requests


def _extract_doi(elocationid: str | None) -> str | None:
    if not elocationid:
        return None
    raw = str(elocationid).strip()
    if raw.lower().startswith("doi:"):
        raw = raw[4:].strip()
    if "/" in raw:
        return f"https://doi.org/{raw}"
    return None


def search_pubmed(query: str, retmax: int = 10) -> list[dict]:
    esearch = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "retmode": "json", "term": query, "retmax": retmax},
        timeout=30,
    )
    esearch.raise_for_status()
    ids = esearch.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    summary = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)},
        timeout=30,
    )
    summary.raise_for_status()
    payload = summary.json().get("result", {})

    out = []
    for pmid in ids:
        item = payload.get(pmid, {})
        doi_url = _extract_doi(item.get("elocationid"))
        out.append(
            {
                "source": "pubmed",
                "title": item.get("title"),
                "doi": item.get("elocationid"),
                "url": doi_url or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
    return out