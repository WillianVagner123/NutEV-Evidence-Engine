from nutev.pipelines.master_pipeline import _canonical_article_key, _dedup_rows


def test_canonical_article_key_prefers_normalized_doi():
    row = {
        "doi": "https://doi.org/10.1000/ABC.1",
        "url": "https://example.org/guideline",
        "title": "Clinical practice guideline",
        "year": 2024,
    }

    assert _canonical_article_key(row) == ("doi", "10.1000/abc.1")


def test_canonical_article_key_prefers_normalized_url_before_title_year():
    row = {
        "url": "HTTPS://Example.org/guideline/?utm_source=newsletter",
        "title": "Clinical practice guideline",
        "year": 2024,
    }

    assert _canonical_article_key(row) == ("url", "https://example.org/guideline")


def test_dedup_rows_keeps_title_only_records_without_year_separate():
    rows = [
        {
            "title": "Lifestyle medicine implementation study",
            "year": "",
            "url": "",
        },
        {
            "title": "Lifestyle medicine implementation study",
            "year": None,
            "url": "",
        },
    ]

    assert _canonical_article_key(rows[0])[0] == "row_hash"
    assert _canonical_article_key(rows[1])[0] == "row_hash"
    assert len(_dedup_rows(rows)) == 2


def test_dedup_rows_merges_records_with_same_normalized_url():
    rows = [
        {
            "title": "Guideline overview",
            "url": "https://example.org/path/?ref=abc",
        },
        {
            "title": "Guideline overview update",
            "url": "https://example.org/path/",
        },
    ]

    assert len(_dedup_rows(rows)) == 1
