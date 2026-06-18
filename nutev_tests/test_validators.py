from nutev.engine.validators import canonical_document_key, normalize_url


def test_normalize_url_removes_tracking_and_default_host_noise() -> None:
    first = "https://www.example.org:443/path/?utm_source=newsletter&b=2&a=1"
    second = "https://example.org/path?a=1&b=2"

    assert normalize_url(first) == normalize_url(second)
    assert normalize_url(first) == "https://example.org/path?a=1&b=2"


def test_canonical_document_key_dedupes_equivalent_urls() -> None:
    first = {
        "url": "https://www.example.org:443/guideline/?utm_medium=email&ref=abc",
        "title": "Nutrition guideline",
        "year": 2026,
    }
    second = {
        "url": "https://example.org/guideline?ref=abc",
        "title": "Nutrition guideline",
        "year": 2026,
    }

    assert canonical_document_key(first) == canonical_document_key(second)
