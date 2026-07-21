"""arXiv preprint connector: Atom XML normalization + reproducible default + pagination.

Same contract as the other bibliographic connectors: single-page default,
deeper recall opt-in via max_results / NUTEV_ARXIV_MAX_RESULTS, cross-page
dedup, normalized to the shared row schema. Atom XML is parsed with the stdlib.
"""
from __future__ import annotations

import nutev.search.arxiv as arxiv

_FEED_HEAD = (
    '<feed xmlns="http://www.w3.org/2005/Atom" '
    'xmlns:arxiv="http://arxiv.org/schemas/atom">'
)


class _Resp:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


def _entry(arxiv_id, title, doi=None, authors=("Silva J", "Doe A"), journal=None, published="2026-02-15T00:00:00Z"):
    author_xml = "".join(f"<author><name>{a}</name></author>" for a in authors)
    doi_xml = f"<arxiv:doi>{doi}</arxiv:doi>" if doi else ""
    journal_xml = f"<arxiv:journal_ref>{journal}</arxiv:journal_ref>" if journal else ""
    return (
        "<entry>"
        f"<id>http://arxiv.org/abs/{arxiv_id}</id>"
        f"<title>{title}</title>"
        "<summary>An abstract.</summary>"
        f"<published>{published}</published>"
        f'<link title="pdf" href="http://arxiv.org/pdf/{arxiv_id}" type="application/pdf"/>'
        f"{author_xml}{doi_xml}{journal_xml}"
        "</entry>"
    )


def _feed(entries):
    return (_FEED_HEAD + "".join(entries) + "</feed>").encode("utf-8")


def test_normalizes_to_shared_schema(monkeypatch):
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(
        arxiv.requests, "get",
        lambda *a, **k: _Resp(_feed([_entry("2401.01234v2", "Diet preprint", doi="10.1/a", journal="J Nutr")])),
    )
    r = arxiv.search_arxiv("diet")[0]
    assert r["source_provider"] == "arxiv"
    assert r["title"] == "Diet preprint"
    assert r["doi"] == "10.1/a"
    assert r["authors"] == "Silva J; Doe A"
    assert r["url"] == "http://arxiv.org/pdf/2401.01234v2"
    assert r["registry_id"] == "arXiv:2401.01234v2"
    assert r["article_type"] == "preprint"
    assert r["year"] == "2026"
    assert r["journal"] == "J Nutr"
    assert r["query"] == "diet"


def test_default_is_single_page(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(params)
        return _Resp(_feed([_entry("2401.1", "A", doi="10.1/a")]))

    monkeypatch.delenv("NUTEV_ARXIV_MAX_RESULTS", raising=False)
    monkeypatch.setattr(arxiv.requests, "get", fake_get)
    rows = arxiv.search_arxiv("diet", page_size=18)
    assert len(calls) == 1 and calls[0]["start"] == 0
    assert calls[0]["search_query"] == "all:diet"
    assert len(rows) == 1


def test_pagination_collects_across_pages_and_dedups(monkeypatch):
    pages = [
        _feed([_entry("2401.1", "A", doi="10.1/a"), _entry("2401.2", "B", doi="10.1/b")]),
        _feed([_entry("2401.2", "B-dup", doi="10.1/b"), _entry("2401.3", "C", doi="10.1/c")]),
    ]
    seq = iter(pages)
    monkeypatch.setattr(arxiv.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = arxiv.search_arxiv("diet", page_size=2, max_results=3)
    assert [r["doi"] for r in rows] == ["10.1/a", "10.1/b", "10.1/c"]


def test_dedup_by_arxiv_id_when_no_doi(monkeypatch):
    pages = [
        _feed([_entry("2401.1", "A", doi=None), _entry("2401.2", "B", doi=None)]),
        _feed([_entry("2401.2", "B-dup", doi=None), _entry("2401.3", "C", doi=None)]),
    ]
    seq = iter(pages)
    monkeypatch.setattr(arxiv.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = arxiv.search_arxiv("diet", page_size=2, max_results=3)
    assert [r["registry_id"] for r in rows] == ["arXiv:2401.1", "arXiv:2401.2", "arXiv:2401.3"]


def test_short_page_terminates(monkeypatch):
    seq = iter([_feed([_entry("2401.1", "A", doi="10.1/a")])])  # 1 < requested 5 → stop
    monkeypatch.setattr(arxiv.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = arxiv.search_arxiv("diet", page_size=5, max_results=50)
    assert [r["doi"] for r in rows] == ["10.1/a"]


def test_network_disabled_and_skip(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert arxiv.search_arxiv("q") == []
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK")
    monkeypatch.setenv("NUTEV_SKIP_ARXIV", "1")
    assert arxiv.search_arxiv("q") == []


def test_wired_into_the_orchestrator_registry():
    from nutev.search.provider_orchestrator import _registry, implemented_search_providers

    assert "arxiv" in _registry()
    assert "arxiv" in implemented_search_providers()
