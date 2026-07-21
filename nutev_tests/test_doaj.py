"""DOAJ open-access connector: normalization + reproducible default + pagination.

Same contract as the other bibliographic connectors: single-page default (no
paging param beyond page 1), deeper recall opt-in via max_results /
NUTEV_DOAJ_MAX_RESULTS, cross-page dedup, normalized to the shared row schema.
"""
from __future__ import annotations

import nutev.search.doaj as doaj


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _item(title, doi=None, authors=None, journal="J OA", year="2026", url=None):
    bib = {"title": title, "year": year, "journal": {"title": journal}, "abstract": "abs"}
    if doi:
        bib["identifier"] = [{"type": "doi", "id": doi}]
    if authors:
        bib["author"] = [{"name": a} for a in authors]
    if url:
        bib["link"] = [{"url": url}]
    return {"bibjson": bib}


def _page(items, total=None):
    return {"results": items, "total": total if total is not None else len(items)}


def test_normalizes_to_shared_schema(monkeypatch):
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(
        doaj.requests, "get",
        lambda *a, **k: _Resp(_page([_item("Mediterranean diet review", doi="10.1/a", authors=["Silva J", "Doe A"], url="https://oa.org/a")])),
    )
    rows = doaj.search_doaj("diet")
    r = rows[0]
    assert r["source_provider"] == "doaj"
    assert r["title"] == "Mediterranean diet review"
    assert r["doi"] == "10.1/a"
    assert r["authors"] == "Silva J; Doe A"
    assert r["journal"] == "J OA"
    assert r["url"] == "https://oa.org/a"
    assert r["is_open_access"] == "true"
    assert r["query"] == "diet"


def test_url_falls_back_to_doi(monkeypatch):
    monkeypatch.setattr(doaj.requests, "get", lambda *a, **k: _Resp(_page([_item("X", doi="10.1/b")])))
    assert doaj.search_doaj("q")[0]["url"] == "https://doi.org/10.1/b"


def test_default_is_single_page(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(params)
        return _Resp(_page([_item("A", doi="10.1/a")], total=500))

    monkeypatch.delenv("NUTEV_DOAJ_MAX_RESULTS", raising=False)
    monkeypatch.setattr(doaj.requests, "get", fake_get)
    rows = doaj.search_doaj("diet", page_size=18)
    assert len(calls) == 1 and calls[0]["page"] == 1
    assert len(rows) == 1


def test_pagination_collects_across_pages_and_dedups(monkeypatch):
    pages = [
        _page([_item("A", doi="10.1/a"), _item("B", doi="10.1/b")], total=100),
        _page([_item("B-dup", doi="10.1/b"), _item("C", doi="10.1/c")], total=100),
    ]
    seq = iter(pages)
    monkeypatch.setattr(doaj.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = doaj.search_doaj("diet", page_size=2, max_results=3)
    assert [r["doi"] for r in rows] == ["10.1/a", "10.1/b", "10.1/c"]


def test_short_page_terminates(monkeypatch):
    seq = iter([_page([_item("A", doi="10.1/a")], total=100)])  # 1 < requested 5 → stop
    monkeypatch.setattr(doaj.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = doaj.search_doaj("diet", page_size=5, max_results=50)
    assert [r["doi"] for r in rows] == ["10.1/a"]


def test_network_disabled_and_skip(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert doaj.search_doaj("q") == []
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK")
    monkeypatch.setenv("NUTEV_SKIP_DOAJ", "1")
    assert doaj.search_doaj("q") == []


def test_doaj_is_wired_into_the_orchestrator_registry():
    from nutev.search.provider_orchestrator import _registry, implemented_search_providers

    assert "doaj" in _registry()
    assert "doaj" in implemented_search_providers()
