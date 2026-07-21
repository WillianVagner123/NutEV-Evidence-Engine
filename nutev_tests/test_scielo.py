"""SciELO connector: SciELO content via the Crossref API (prefix 10.1590)."""
from __future__ import annotations

import nutev.search.scielo as scielo


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _item(title, doi):
    return {"title": [title], "DOI": doi, "container-title": ["Rev Saude Publica"], "author": [{"given": "A", "family": "Silva"}]}


def _page(items):
    return {"message": {"items": items}}


def test_restricts_to_scielo_prefix_and_retags(monkeypatch):
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    captured = {}

    def fake_get(url, params=None, timeout=None, headers=None):
        captured.update(params)
        return _Resp(_page([_item("Dieta e saúde", "10.1590/abc")]))

    monkeypatch.setattr(scielo.requests, "get", fake_get)
    rows = scielo.search_scielo("dieta")
    assert captured["filter"] == "prefix:10.1590"   # scoped to SciELO
    r = rows[0]
    assert r["source_provider"] == "scielo"
    assert r["metadata_status"] == "scielo_search"
    assert r["doi"] == "10.1590/abc"
    assert r["title"] == "Dieta e saúde"
    assert r["query"] == "dieta"


def test_default_single_page_no_offset(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(params)
        return _Resp(_page([_item("A", "10.1590/a")]))

    monkeypatch.delenv("NUTEV_SCIELO_MAX_RESULTS", raising=False)
    monkeypatch.setattr(scielo.requests, "get", fake_get)
    scielo.search_scielo("q", rows=18)
    assert len(calls) == 1 and calls[0]["offset"] == 0


def test_pagination_and_dedup(monkeypatch):
    pages = [
        _page([_item("A", "10.1590/a"), _item("B", "10.1590/b")]),
        _page([_item("B-dup", "10.1590/b"), _item("C", "10.1590/c")]),
    ]
    seq = iter(pages)
    monkeypatch.setattr(scielo.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = scielo.search_scielo("q", rows=2, max_results=3)
    assert [r["doi"] for r in rows] == ["10.1590/a", "10.1590/b", "10.1590/c"]


def test_network_disabled_and_skip(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert scielo.search_scielo("q") == []
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK")
    monkeypatch.setenv("NUTEV_SKIP_SCIELO", "1")
    assert scielo.search_scielo("q") == []


def test_both_wired_into_the_registry():
    from nutev.search.provider_orchestrator import _registry, implemented_search_providers

    for pid in ("clinicaltrials", "scielo"):
        assert pid in _registry()
        assert pid in implemented_search_providers()
