from nutev.analysis.relevance import keep_candidate_for_download, score_record
from nutev.download.downloader import _failure_reason, _primary_download_url
from nutev.download.resolver import _extract_pdf_like_link, extract_clean_doi, normalize_candidate_url


def test_extract_pdf_like_link_reads_citation_pdf_meta():
    html = '<html><head><meta name="citation_pdf_url" content="/article.pdf"></head></html>'

    assert _extract_pdf_like_link("https://example.org/paper", html) == "https://example.org/article.pdf"


def test_extract_pdf_like_link_reads_anchor_text():
    html = '<a href="/download/123">Download PDF</a>'

    assert _extract_pdf_like_link("https://example.org/paper", html) == "https://example.org/download/123"


def test_dirty_pii_doi_text_normalizes_to_clean_doi_url():
    dirty = "pii: nuaf273. doi: 10.1093/nutrit/nuaf273"

    assert extract_clean_doi(dirty) == "10.1093/nutrit/nuaf273"
    assert normalize_candidate_url(f"https://doi.org/{dirty}") == "https://doi.org/10.1093/nutrit/nuaf273"


def test_pubmed_landing_without_doi_is_not_primary_download_target():
    record = {"source": "pubmed", "doi": ""}

    assert _primary_download_url(record, "https://pubmed.ncbi.nlm.nih.gov/42107936/") is None


def test_pubmed_landing_with_doi_uses_doi_as_primary_target():
    record = {"source": "pubmed", "doi": "10.1056/NEJMoa1511939"}

    assert _primary_download_url(record, "https://pubmed.ncbi.nlm.nih.gov/42107936/") == "https://doi.org/10.1056/NEJMoa1511939"


def test_blocked_host_failure_reason_is_specific():
    reason = _failure_reason(Exception("blocked"), "https://www.mdpi.com/2072-6643/17/23/3782", 403)

    assert reason == "blocked_mdpi"


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
