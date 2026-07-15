"""P2.2 — tests for the full-text resolver (mocked network)."""
from __future__ import annotations

from nutev.acquire.fulltext_resolver import resolve_fulltext, resolve_many


class _Resp:
    def __init__(self, payload, code=200):
        self._p, self.status_code = payload, code

    def json(self):
        return self._p


class _Session:
    """Routes by URL: Unpaywall and elink, configurable per DOI/PMID."""

    def __init__(self, unpaywall=None, elink=None):
        self.unpaywall = unpaywall or {}   # doi -> pdf url (OA) or None
        self.elink = elink or {}           # pmid -> pmcid
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        if "unpaywall.org" in url:
            doi = url.split("/v2/")[1].split("?")[0]
            pdf = self.unpaywall.get(doi)
            return _Resp({"is_oa": bool(pdf), "best_oa_location": {"url_for_pdf": pdf} if pdf else None})
        if "elink.fcgi" in url:
            pmid = url.split("id=")[1].split("&")[0]
            pmcid = self.elink.get(pmid)
            links = [{"dbto": "pmc", "links": [pmcid.replace("PMC", "")]}] if pmcid else []
            return _Resp({"linksets": [{"linksetdbs": links}]})
        return _Resp({}, code=404)


def test_existing_pmcid_needs_no_network():
    r = resolve_fulltext({"pmcid": "PMC123"})
    assert r["fulltext_status"] == "fulltext_oa"
    assert r["retrieval_method"] == "existing_pmcid"
    assert "PMC123" in r["fulltext_url"]


def test_needs_network_without_session():
    r = resolve_fulltext({"doi": "10.1/x"})
    assert r["fulltext_status"] == "needs_network"


def test_doi_resolves_via_unpaywall():
    s = _Session(unpaywall={"10.1/oa": "http://oa/pdf"})
    r = resolve_fulltext({"doi": "10.1/OA"}, email="me@x.org", session=s)
    assert r["fulltext_status"] == "fulltext_oa"
    assert r["retrieval_method"] == "unpaywall"
    assert r["fulltext_url"] == "http://oa/pdf"


def test_pmid_resolves_via_elink_when_no_oa_doi():
    s = _Session(unpaywall={}, elink={"999": "PMC777"})
    r = resolve_fulltext({"doi": "10.2/paywalled", "pmid": "999"}, email="me@x.org", session=s)
    assert r["fulltext_status"] == "fulltext_oa"
    assert r["retrieval_method"] == "pmc_elink"
    assert r["pmcid"] == "PMC777"


def test_paywall_when_no_oa_anywhere():
    s = _Session(unpaywall={}, elink={})
    r = resolve_fulltext({"doi": "10.3/pay", "pmid": "5"}, email="me@x.org", session=s)
    assert r["fulltext_status"] == "paywall"
    assert r["retrieval_method"] == "none"


def test_resolve_many_shares_cache():
    s = _Session(unpaywall={"10.1/oa": "http://oa/pdf"})
    recs = [{"doi": "10.1/oa"}, {"doi": "10.1/oa"}]  # same DOI twice
    resolve_many(recs, email="me@x.org", session=s)
    assert all(r["fulltext_status"] == "fulltext_oa" for r in recs)
    # Unpaywall queried once thanks to the shared cache.
    assert sum(1 for c in s.calls if "unpaywall" in c) == 1
