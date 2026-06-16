from __future__ import annotations

import nutev.download.oa_resolver as oa
from nutev.download.oa_resolver import pmc_pdf_url, resolve_oa_pdf, unpaywall_pdf_url


class _Resp:
    def __init__(self, status: int, payload: dict):
        self.status_code = status
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def test_record_oa_pdf_url_takes_precedence(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("network should not be touched when oa_pdf_url is present")

    monkeypatch.setattr(oa.requests, "get", _boom)
    record = {"oa_pdf_url": "https://example.org/paper.pdf", "doi": "10.1/x"}
    assert resolve_oa_pdf(record) == "https://example.org/paper.pdf"


def test_unpaywall_returns_best_oa_pdf(monkeypatch):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "researcher@example.org")
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    payload = {"best_oa_location": {"url_for_pdf": "https://oa.example.org/full.pdf"}}
    monkeypatch.setattr(oa.requests, "get", lambda *a, **k: _Resp(200, payload))
    assert unpaywall_pdf_url("https://doi.org/10.1234/ABC") == "https://oa.example.org/full.pdf"


def test_unpaywall_requires_email_and_doi(monkeypatch):
    monkeypatch.delenv("UNPAYWALL_EMAIL", raising=False)
    monkeypatch.delenv("NCBI_EMAIL", raising=False)
    monkeypatch.delenv("ENTREZ_EMAIL", raising=False)
    monkeypatch.delenv("CROSSREF_MAILTO", raising=False)
    monkeypatch.delenv("OPENALEX_MAILTO", raising=False)
    assert unpaywall_pdf_url("10.1/x") is None  # no contact email
    assert unpaywall_pdf_url(None, "a@b.org") is None  # no doi


def test_pmc_pdf_url():
    assert pmc_pdf_url("PMC1234567") == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/pdf/"
    assert pmc_pdf_url("1234567") == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/pdf/"
    assert pmc_pdf_url("") is None


def test_resolve_oa_pdf_disabled_network(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert resolve_oa_pdf({"doi": "10.1/x", "pmcid": "PMC9"}) is None
