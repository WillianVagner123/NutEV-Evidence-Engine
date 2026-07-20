"""Crossref (offset) and OpenAlex (cursor) bounded pagination (T7 tranche 2).

Same contract as Europe PMC: default path unchanged (single page, no paging
param) for reproducibility; deeper recall is opt-in via max_results / env, with
cross-page de-duplication and safe termination.
"""
from __future__ import annotations

import nutev.search.crossref as cr
import nutev.search.openalex as oa


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


# --------------------------------------------------------------------------- #
# Crossref (offset paging)
# --------------------------------------------------------------------------- #

def _cr_page(items):
    return {"message": {"items": items}}


def test_crossref_default_single_page_sends_no_offset(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(params)
        return _Resp(_cr_page([{"DOI": "10.1/a", "title": ["A"]}]))

    monkeypatch.delenv("NUTEV_CROSSREF_MAX_RESULTS", raising=False)
    monkeypatch.setattr(cr.requests, "get", fake_get)

    rows = cr.search_crossref("diet", rows=18)
    assert len(calls) == 1
    assert "offset" not in calls[0]
    assert rows[0]["doi"] == "10.1/a"


def test_crossref_paginates_offset_and_dedups(monkeypatch):
    pages = [
        _cr_page([{"DOI": "10.1/a", "title": ["A"]}, {"DOI": "10.1/b", "title": ["B"]}]),
        _cr_page([{"DOI": "10.1/b", "title": ["B-dup"]}, {"DOI": "10.1/c", "title": ["C"]}]),
    ]
    seq = iter(pages)
    offsets = []

    def fake_get(url, params=None, timeout=None, headers=None):
        offsets.append(params.get("offset"))
        return _Resp(next(seq))

    monkeypatch.setattr(cr.requests, "get", fake_get)

    rows = cr.search_crossref("diet", rows=2, max_results=3)
    assert [r["doi"] for r in rows] == ["10.1/a", "10.1/b", "10.1/c"]  # dedup kept 3 unique
    assert offsets == [0, 2]


def test_crossref_stops_on_short_last_page(monkeypatch):
    # A page smaller than requested means no more results -> stop (no infinite loop).
    seq = iter([_cr_page([{"DOI": "10.1/a", "title": ["A"]}])])
    monkeypatch.setattr(cr.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = cr.search_crossref("diet", rows=5, max_results=50)
    assert [r["doi"] for r in rows] == ["10.1/a"]


# --------------------------------------------------------------------------- #
# OpenAlex (cursor paging)
# --------------------------------------------------------------------------- #

def _oa_page(results, next_cursor):
    return {"results": results, "meta": {"next_cursor": next_cursor}}


def test_openalex_default_single_page_sends_no_cursor(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(params)
        return _Resp(_oa_page([{"id": "W1", "display_name": "A"}], "c2"))

    monkeypatch.delenv("NUTEV_OPENALEX_MAX_RESULTS", raising=False)
    monkeypatch.setattr(oa.requests, "get", fake_get)

    rows = oa.search_openalex("diet", per_page=12)
    assert len(calls) == 1
    assert "cursor" not in calls[0]
    assert rows[0]["title"] == "A"


def test_openalex_paginates_cursor_and_caps(monkeypatch):
    pages = [
        _oa_page([{"id": "W1", "display_name": "A"}, {"id": "W2", "display_name": "B"}], "c2"),
        _oa_page([{"id": "W3", "display_name": "C"}, {"id": "W4", "display_name": "D"}], "c3"),
    ]
    seq = iter(pages)
    monkeypatch.setattr(oa.requests, "get", lambda *a, **k: _Resp(next(seq)))

    rows = oa.search_openalex("diet", per_page=2, max_results=3)
    assert [r["title"] for r in rows] == ["A", "B", "C"]


def test_openalex_stops_on_repeated_cursor(monkeypatch):
    pages = [
        _oa_page([{"id": "W1", "display_name": "A"}], "c2"),
        _oa_page([{"id": "W1", "display_name": "A-dup"}, {"id": "W2", "display_name": "B"}], "c2"),
    ]
    seq = iter(pages)
    monkeypatch.setattr(oa.requests, "get", lambda *a, **k: _Resp(next(seq)))

    rows = oa.search_openalex("diet", per_page=5, max_results=50)
    assert [r["title"] for r in rows] == ["A", "B"]  # cursor repeat halts; dedup on id
