from __future__ import annotations

from nutev.search.crossref import _normalize_crossref, search_crossref

EXPECTED_KEYS = {
    "source",
    "source_provider",
    "title",
    "abstract",
    "snippet",
    "doi",
    "pmid",
    "pmcid",
    "url",
    "journal",
    "year",
    "publication_date",
    "article_type",
    "authors",
    "publisher",
    "issn",
    "language",
    "affiliations",
    "metadata_status",
    "query",
    "provider_query",
}


def _sample_item() -> dict:
    return {
        "title": ["Dietary patterns and cardiovascular outcomes"],
        "DOI": "10.1000/abc123",
        "container-title": ["Journal of Nutrition"],
        "type": "journal-article",
        "publisher": "Oxford University Press",
        "ISSN": ["1234-5678", "8765-4321"],
        "language": "en",
        "published-print": {"date-parts": [[2021, 5]]},
        "abstract": "<jats:p>Study abstract.</jats:p>",
        "author": [
            {
                "given": "Ana",
                "family": "Costa",
                "affiliation": [{"name": "University of Sao Paulo, Brazil"}],
            },
            {
                "given": "John",
                "family": "Doe",
                "affiliation": [{"name": "University of Oxford, United Kingdom"}],
            },
        ],
    }


def test_normalize_crossref_has_all_keys():
    row = _normalize_crossref(_sample_item(), "q")
    assert set(row.keys()) == EXPECTED_KEYS


def test_normalize_crossref_new_fields():
    row = _normalize_crossref(_sample_item(), "cardiovascular nutrition")
    assert row["publisher"] == "Oxford University Press"
    assert row["issn"] == "1234-5678"  # first ISSN only
    assert row["language"] == "en"
    assert row["affiliations"] == [
        "University of Sao Paulo, Brazil",
        "University of Oxford, United Kingdom",
    ]


def test_normalize_crossref_preserves_existing_fields():
    row = _normalize_crossref(_sample_item(), "cardiovascular nutrition")
    assert row["source"] == "crossref"
    assert row["source_provider"] == "crossref"
    assert row["metadata_status"] == "crossref_search"
    assert row["title"] == "Dietary patterns and cardiovascular outcomes"
    assert row["doi"] == "10.1000/abc123"
    assert row["journal"] == "Journal of Nutrition"
    assert row["year"] == "2021"
    assert row["publication_date"] == "2021-5"
    assert row["article_type"] == "journal-article"
    assert row["authors"] == "Ana Costa; John Doe"
    assert row["url"] == "https://doi.org/10.1000/abc123"
    assert row["query"] == "cardiovascular nutrition"
    assert row["provider_query"] == "cardiovascular nutrition"


def test_normalize_crossref_missing_fields_use_safe_defaults():
    row = _normalize_crossref({}, "q")
    assert set(row.keys()) == EXPECTED_KEYS
    assert row["publisher"] == ""
    assert row["issn"] == ""
    assert row["language"] == ""
    assert row["affiliations"] == []  # commonly empty in Crossref
    assert row["title"] == ""
    assert row["authors"] == ""


def test_search_crossref_disabled_network(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert search_crossref("anything") == []
