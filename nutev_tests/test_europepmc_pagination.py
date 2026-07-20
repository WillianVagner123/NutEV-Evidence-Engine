"""Europe PMC connector: bounded cursorMark pagination + reproducible default (T7).

The default path is unchanged (single page of ``page_size``, no cursorMark), so
existing runs stay reproducible; deeper recall is opt-in via ``max_results`` /
``NUTEV_EUROPEPMC_MAX_RESULTS`` and walks cursorMark with cross-page dedup.
"""
from __future__ import annotations

import nutev.search.europepmc as epmc


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _page(results, next_cursor):
    return {"resultList": {"result": results}, "nextCursorMark": next_cursor}


def test_default_is_single_page_and_sends_no_cursor(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(params)
        return _Resp(_page([{"title": "A", "doi": "10.1/a"}], "next"))

    monkeypatch.delenv("NUTEV_EUROPEPMC_MAX_RESULTS", raising=False)
    monkeypatch.setattr(epmc.requests, "get", fake_get)

    rows = epmc.search_europepmc("diet", page_size=18)

    assert len(calls) == 1                       # exactly one request
    assert "cursorMark" not in calls[0]          # historical request shape preserved
    assert rows[0]["title"] == "A"
    assert rows[0]["query"] == "diet"


def test_pagination_collects_across_pages_up_to_max(monkeypatch):
    pages = [
        _page([{"id": "1", "title": "A"}, {"id": "2", "title": "B"}], "c2"),
        _page([{"id": "3", "title": "C"}, {"id": "4", "title": "D"}], "c3"),
    ]
    seq = iter(pages)

    def fake_get(url, params=None, timeout=None):
        assert params.get("cursorMark")         # paginated path uses cursorMark
        return _Resp(next(seq))

    monkeypatch.setattr(epmc.requests, "get", fake_get)

    rows = epmc.search_europepmc("diet", page_size=2, max_results=3)

    assert [r["title"] for r in rows] == ["A", "B", "C"]   # capped at 3


def test_pagination_dedups_and_stops_on_repeated_cursor(monkeypatch):
    # Same cursor returned twice → loop must terminate (no infinite paging), and a
    # duplicate id across pages is collected only once.
    pages = [
        _page([{"id": "1", "title": "A"}], "c2"),
        _page([{"id": "1", "title": "A-dup"}, {"id": "2", "title": "B"}], "c2"),
    ]
    seq = iter(pages)

    def fake_get(url, params=None, timeout=None):
        return _Resp(next(seq))

    monkeypatch.setattr(epmc.requests, "get", fake_get)

    rows = epmc.search_europepmc("diet", page_size=5, max_results=50)

    titles = [r["title"] for r in rows]
    assert titles == ["A", "B"]                 # id "1" not duplicated


def test_env_opts_into_pagination(monkeypatch):
    monkeypatch.setenv("NUTEV_EUROPEPMC_MAX_RESULTS", "3")
    pages = [
        _page([{"id": "1", "title": "A"}, {"id": "2", "title": "B"}], "c2"),
        _page([{"id": "3", "title": "C"}, {"id": "4", "title": "D"}], "c3"),
    ]
    seq = iter(pages)
    monkeypatch.setattr(epmc.requests, "get", lambda *a, **k: _Resp(next(seq)))

    rows = epmc.search_europepmc("diet", page_size=2)  # no explicit max_results
    assert len(rows) == 3


def test_network_disabled_returns_empty(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    rows = epmc.search_europepmc("diet")
    assert rows == []
