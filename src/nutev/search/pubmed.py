from __future__ import annotations
import requests
import time


def _extract_doi(elocationid: str | None) -> str | None:
    if not elocationid:
        return None
    raw = str(elocationid).strip()
    if raw.lower().startswith("doi:"):
        raw = raw[4:].strip()
    if "/" in raw:
        return f"https://doi.org/{raw}"
    return None


def search_pubmed(query: str, retmax: int = 18) -> list[dict]:
    import os
    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return []
    last = None
    for attempt in range(1, 4):
        try:
            esearch = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={"db": "pubmed", "retmode": "json", "term": query, "retmax": retmax},
                timeout=45,
            )
            esearch.raise_for_status()
            ids = esearch.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []

            summary = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)},
                timeout=45,
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
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    raise last