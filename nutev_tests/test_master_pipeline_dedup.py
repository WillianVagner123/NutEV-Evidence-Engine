from __future__ import annotations

from nutev.pipelines.master_pipeline import _dedup_rows, _normalize_url


def test_normalize_url_ignores_scheme_www_and_default_ports() -> None:
    assert _normalize_url("https://www.Example.org:443/path/to/doc/?utm_source=x") == "example.org/path/to/doc"
    assert _normalize_url("http://example.org:80/path/to/doc/") == "example.org/path/to/doc"


def test_dedup_rows_merges_http_https_and_www_url_variants() -> None:
    rows = [
        {
            "title": "Lifestyle intervention for cardiometabolic risk",
            "url": "http://www.example.org/guideline/full-text/",
            "source": "openalex",
        },
        {
            "title": "Lifestyle intervention for cardiometabolic risk",
            "url": "https://example.org/guideline/full-text?download=1",
            "source": "crossref",
        },
    ]

    deduped = _dedup_rows(rows)

    assert len(deduped) == 1
