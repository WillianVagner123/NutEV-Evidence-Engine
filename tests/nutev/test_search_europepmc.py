from __future__ import annotations

from nutev.search.europepmc import search_europepmc


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_search_europepmc_normalizes_metadata(monkeypatch) -> None:
    payload = {
        "resultList": {
            "result": [
                {
                    "title": "Lifestyle medicine for MASLD",
                    "abstractText": "Systematic review of food is medicine strategies.",
                    "doi": "10.1000/example-doi",
                    "pmid": "12345678",
                    "pmcid": "1234567",
                    "journalTitle": "Nutrition Reviews",
                    "pubYear": "2025",
                    "firstPublicationDate": "2025-01-15",
                    "pubType": "Systematic Review",
                    "authorString": "Doe J; Smith A",
                    "isOpenAccess": "Y",
                    "fullTextUrlList": {
                        "fullTextUrl": [
                            {
                                "availability": "Open access",
                                "documentStyle": "html",
                                "url": "https://example.org/fulltext"
                            }
                        ]
                    },
                }
            ]
        }
    }

    def _fake_get(*args, **kwargs):
        return _FakeResponse(payload)

    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr("nutev.search.europepmc.requests.get", _fake_get)

    rows = search_europepmc("masld food is medicine", page_size=5)

    assert len(rows) == 1
    row = rows[0]
    assert row["source"] == "europepmc"
    assert row["title"] == "Lifestyle medicine for MASLD"
    assert row["abstract"] == "Systematic review of food is medicine strategies."
    assert row["summary"] == row["abstract"]
    assert row["doi"] == "10.1000/example-doi"
    assert row["pmid"] == "12345678"
    assert row["pmcid"] == "PMC1234567"
    assert row["url"] == "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/"
    assert row["journal"] == "Nutrition Reviews"
    assert row["year"] == "2025"
    assert row["publication_date"] == "2025-01-15"
    assert row["article_type"] == "Systematic Review"
    assert row["authors"] == "Doe J; Smith A"
    assert row["metadata_status"] == "europepmc_search"
    assert row["is_open_access"] == "y"
