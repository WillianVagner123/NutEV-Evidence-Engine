from __future__ import annotations

from nutev.export.curation import _compute_document_key, _normalize_url


def test_normalize_url_ignores_scheme_www_and_tracking_params() -> None:
    canonical = _normalize_url(
        "https://www.Example.org/path/to/doc/?utm_source=newsletter#section"
    )

    assert canonical == "example.org/path/to/doc"
    assert canonical == _normalize_url("http://example.org/path/to/doc")
    assert canonical == _normalize_url("https://example.org:443/path/to/doc/")


def test_compute_document_key_uses_canonical_url_before_title_year() -> None:
    first = {
        "title": "NutMEV guideline",
        "year": "2024",
        "final_url": "https://www.example.org/guideline/?ref=abc",
    }
    second = {
        "title": "NutMEV guideline",
        "year": "2024",
        "final_url": "http://example.org/guideline",
    }

    assert _compute_document_key(first) == ("example.org/guideline", "url")
    assert _compute_document_key(first) == _compute_document_key(second)
