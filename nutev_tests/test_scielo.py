from __future__ import annotations

from nutev.search.scielo import _normalize_scielo, search_scielo

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
    "metadata_status",
    "query",
    "provider_query",
    "oa_pdf_url",
    "is_open_access",
}


def _sample_item() -> dict:
    return {
        "title": ["Consumo alimentar e saúde cardiovascular"],
        "DOI": "10.1590/S1234-56782020000100001",
        "container-title": ["Revista de Saúde Pública"],
        "type": "journal-article",
        "author": [
            {"given": "Maria", "family": "Silva"},
            {"given": "João", "family": "Souza"},
        ],
        "published-print": {"date-parts": [[2020, 1]]},
        "abstract": "<jats:p>Resumo do estudo.</jats:p>",
        "URL": "https://example.org/article",
    }


def test_normalize_scielo_maps_fields():
    row = _normalize_scielo(_sample_item(), "cardiovascular nutrition")

    assert row["source"] == "scielo"
    assert row["source_provider"] == "scielo"
    assert row["metadata_status"] == "scielo_search"
    # DOI bare + lowercased.
    assert row["doi"] == "10.1590/s1234-56782020000100001"
    assert row["title"] == "Consumo alimentar e saúde cardiovascular"
    assert row["journal"] == "Revista de Saúde Pública"
    assert row["authors"] == "Maria Silva; João Souza"
    assert row["year"] == "2020"
    assert row["publication_date"] == "2020-1"
    assert row["article_type"] == "journal-article"
    # JATS abstract left as-is.
    assert "<jats:p>" in row["abstract"]
    assert row["snippet"] == row["abstract"]
    # URL derived from the (lowercased) DOI.
    assert row["url"] == "https://doi.org/10.1590/s1234-56782020000100001"
    assert row["query"] == "cardiovascular nutrition"
    assert row["provider_query"] == "cardiovascular nutrition"
    assert row["is_open_access"] == ""
    assert row["oa_pdf_url"] == ""


def test_normalize_scielo_has_all_keys():
    row = _normalize_scielo(_sample_item(), "q")
    assert set(row.keys()) == EXPECTED_KEYS


def test_normalize_scielo_missing_fields_use_empty_strings():
    row = _normalize_scielo({}, "q")
    assert set(row.keys()) == EXPECTED_KEYS
    assert row["doi"] == ""
    assert row["title"] == ""
    assert row["journal"] == ""
    assert row["authors"] == ""
    assert row["year"] == ""
    assert row["url"] == ""


def test_normalize_scielo_url_falls_back_to_item_url():
    item = _sample_item()
    del item["DOI"]
    row = _normalize_scielo(item, "q")
    assert row["doi"] == ""
    assert row["url"] == "https://example.org/article"


def test_search_scielo_disabled_network(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert search_scielo("nutrition", limit=5) == []
