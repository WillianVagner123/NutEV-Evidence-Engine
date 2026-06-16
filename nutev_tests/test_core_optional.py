from __future__ import annotations

from nutev.search.base import ProviderResult
from nutev.search.core_optional import _normalize_core, search_core


def test_core_skipped_without_key(monkeypatch):
    monkeypatch.delenv("CORE_API_KEY", raising=False)
    result = search_core("diet")
    assert isinstance(result, ProviderResult)
    assert result.status == "skipped"


def test_core_disabled_network_returns_empty(monkeypatch):
    monkeypatch.setenv("CORE_API_KEY", "k")
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert search_core("diet") == []


def test_normalize_core_maps_download_url_and_doi():
    item = {
        "title": "Plant-forward diets",
        "abstract": "A study.",
        "yearPublished": 2024,
        "doi": "https://doi.org/10.1234/ABC",
        "downloadUrl": "https://core.ac.uk/download/1.pdf",
        "authors": [{"name": "Smith J"}, {"name": "Doe A"}],
        "publisher": "Elsevier",
    }
    row = _normalize_core(item, "q")
    assert row["source"] == "core"
    assert row["doi"] == "10.1234/abc"
    assert row["oa_pdf_url"] == "https://core.ac.uk/download/1.pdf"
    assert row["url"] == "https://core.ac.uk/download/1.pdf"
    assert row["is_open_access"] == "true"
    assert row["authors"] == "Smith J; Doe A"
    assert row["year"] == "2024"
