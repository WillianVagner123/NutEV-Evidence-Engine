from nutev.analysis.relevance import keep_candidate_for_download, score_record
from nutev.download.resolver import _extract_pdf_like_link


def test_extract_pdf_like_link_reads_citation_pdf_meta():
    html = '<html><head><meta name="citation_pdf_url" content="/article.pdf"></head></html>'

    assert _extract_pdf_like_link("https://example.org/paper", html) == "https://example.org/article.pdf"


def test_extract_pdf_like_link_reads_anchor_text():
    html = '<a href="/download/123">Download PDF</a>'

    assert _extract_pdf_like_link("https://example.org/paper", html) == "https://example.org/download/123"


def test_open_access_high_value_candidate_is_kept_for_download():
    record = {
        "title": "Clinical practice guideline for obesity management",
        "url": "https://example.org/open-access/article",
        "abstract": "Free full text available from an open access source.",
        "source": "crossref",
    }

    scored = score_record(record, {}, "busca2a")

    assert keep_candidate_for_download(scored, "busca2a")


def test_hard_drop_still_blocks_low_value_article_types():
    record = {
        "title": "Editorial about nutrition guideline",
        "url": "https://example.org/editorial.pdf",
        "source": "crossref",
        "relevance_score": 50,
    }

    assert not keep_candidate_for_download(record, "busca2a")
