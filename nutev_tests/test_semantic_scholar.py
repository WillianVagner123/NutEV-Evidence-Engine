"""Semantic Scholar connector: normalization + reproducible default + offset pagination.

Same contract as the other bibliographic connectors: single-page default,
deeper recall opt-in via max_results / NUTEV_SEMANTIC_SCHOLAR_MAX_RESULTS,
cross-page dedup, normalized to the shared row schema.
"""
from __future__ import annotations

import nutev.search.semantic_scholar as s2


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _paper(title, doi=None, pmid=None, authors=None, venue="J Nutr", year=2026, oa=None, url=None):
    ext = {}
    if doi:
        ext["DOI"] = doi
    if pmid:
        ext["PubMed"] = pmid
    p = {"title": title, "abstract": "abs", "venue": venue, "year": year, "externalIds": ext}
    if authors:
        p["authors"] = [{"name": a} for a in authors]
    if oa:
        p["openAccessPdf"] = {"url": oa}
    if url:
        p["url"] = url
    return p


def _page(papers, nxt=None):
    out = {"data": papers}
    out["next"] = nxt
    return out


def test_normalizes_to_shared_schema(monkeypatch):
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(
        s2.requests, "get",
        lambda *a, **k: _Resp(_page([_paper("Diet review", doi="10.1/a", pmid="123", authors=["Silva J", "Doe A"], oa="https://oa.org/a.pdf")])),
    )
    r = s2.search_semantic_scholar("diet")[0]
    assert r["source_provider"] == "semantic_scholar"
    assert r["title"] == "Diet review"
    assert r["doi"] == "10.1/a"
    assert r["pmid"] == "123"
    assert r["authors"] == "Silva J; Doe A"
    assert r["journal"] == "J Nutr"
    assert r["url"] == "https://oa.org/a.pdf"
    assert r["query"] == "diet"


def test_url_falls_back_to_doi(monkeypatch):
    monkeypatch.setattr(s2.requests, "get", lambda *a, **k: _Resp(_page([_paper("X", doi="10.1/b")])))
    assert s2.search_semantic_scholar("q")[0]["url"] == "https://doi.org/10.1/b"


def test_api_key_header_sent_when_present(monkeypatch):
    monkeypatch.setenv("S2_API_KEY", "secret-key")
    captured = {}

    def fake_get(url, params=None, timeout=None, headers=None):
        captured.update(headers or {})
        return _Resp(_page([_paper("A", doi="10.1/a")]))

    monkeypatch.setattr(s2.requests, "get", fake_get)
    s2.search_semantic_scholar("q")
    assert captured.get("x-api-key") == "secret-key"


def test_no_key_header_when_absent(monkeypatch):
    monkeypatch.delenv("S2_API_KEY", raising=False)
    captured = {}

    def fake_get(url, params=None, timeout=None, headers=None):
        captured.update(headers or {})
        return _Resp(_page([_paper("A", doi="10.1/a")]))

    monkeypatch.setattr(s2.requests, "get", fake_get)
    s2.search_semantic_scholar("q")
    assert "x-api-key" not in captured


def test_default_is_single_page(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(params)
        return _Resp(_page([_paper("A", doi="10.1/a")], nxt=18))

    monkeypatch.delenv("NUTEV_SEMANTIC_SCHOLAR_MAX_RESULTS", raising=False)
    monkeypatch.setattr(s2.requests, "get", fake_get)
    rows = s2.search_semantic_scholar("diet", page_size=18)
    assert len(calls) == 1 and calls[0]["offset"] == 0
    assert len(rows) == 1


def test_pagination_collects_across_pages_and_dedups(monkeypatch):
    pages = [
        _page([_paper("A", doi="10.1/a"), _paper("B", doi="10.1/b")], nxt=2),
        _page([_paper("B-dup", doi="10.1/b"), _paper("C", doi="10.1/c")], nxt=4),
    ]
    seq = iter(pages)
    monkeypatch.setattr(s2.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = s2.search_semantic_scholar("diet", page_size=2, max_results=3)
    assert [r["doi"] for r in rows] == ["10.1/a", "10.1/b", "10.1/c"]


def test_short_page_terminates(monkeypatch):
    seq = iter([_page([_paper("A", doi="10.1/a")], nxt=None)])  # no next → stop
    monkeypatch.setattr(s2.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = s2.search_semantic_scholar("diet", page_size=5, max_results=50)
    assert [r["doi"] for r in rows] == ["10.1/a"]


def test_network_disabled_and_skip(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert s2.search_semantic_scholar("q") == []
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK")
    monkeypatch.setenv("NUTEV_SKIP_SEMANTIC_SCHOLAR", "1")
    assert s2.search_semantic_scholar("q") == []


def test_wired_into_the_orchestrator_registry():
    from nutev.search.provider_orchestrator import _registry, implemented_search_providers

    assert "semantic_scholar" in _registry()
    assert "semantic_scholar" in implemented_search_providers()
