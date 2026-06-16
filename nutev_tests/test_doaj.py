from __future__ import annotations

from nutev.search.doaj import _normalize_doaj, search_doaj

SAMPLE_ITEM = {
    "bibjson": {
        "title": "Whole Food Diets and Metabolic Outcomes",
        "abstract": "B" * 450,
        "year": "2022",
        "journal": {"title": "Open Journal of Nutrition"},
        "author": [
            {"name": "Jane Doe"},
            {"name": "John Smith"},
        ]
        + [{"name": f"Author {i}"} for i in range(20)],
        "identifier": [
            {"type": "pissn", "id": "1234-5678"},
            {"type": "doi", "id": "10.5555/ABC.2022.0042"},
        ],
        "link": [
            {"type": "fulltext", "url": "https://example.org/article/full.pdf"},
        ],
    }
}


def test_normalize_schema_and_values():
    row = _normalize_doaj(SAMPLE_ITEM, "whole food diet")

    expected_keys = {
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
        "metadata_status",
        "query",
        "provider_query",
        "oa_pdf_url",
        "is_open_access",
    }
    assert set(row.keys()) == expected_keys

    assert row["source"] == "doaj"
    assert row["source_provider"] == "doaj"
    assert row["metadata_status"] == "doaj_search"
    assert row["query"] == "whole food diet"
    assert row["provider_query"] == "whole food diet"

    # DOI extracted from identifier list, stripped bare and lowercased.
    assert row["doi"] == "10.5555/abc.2022.0042"

    assert row["pmid"] == ""
    assert row["pmcid"] == ""

    assert row["journal"] == "Open Journal of Nutrition"
    assert row["year"] == "2022"
    assert row["publication_date"] == "2022"

    # article_type is always "" for DOAJ.
    assert row["article_type"] == ""

    # url = first link url; oa_pdf_url = fulltext link.
    assert row["url"] == "https://example.org/article/full.pdf"
    assert row["oa_pdf_url"] == "https://example.org/article/full.pdf"

    # All DOAJ content is open access.
    assert row["is_open_access"] == "true"

    # Authors joined with "; " and capped at 12.
    assert row["authors"].startswith("Jane Doe; John Smith; ")
    assert len(row["authors"].split("; ")) == 12

    # snippet truncated to ~300 chars.
    assert len(row["snippet"]) == 300


def test_normalize_missing_fields_use_empty_strings():
    row = _normalize_doaj({}, "q")
    for key in (
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
        "oa_pdf_url",
    ):
        assert row[key] == ""
    # DOAJ content is always open access regardless of missing fields.
    assert row["is_open_access"] == "true"


def test_search_disabled_network_returns_empty(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert search_doaj("anything") == []
