"""Tests for the P1 full-text recoverability diagnostic."""
from __future__ import annotations

from pathlib import Path

from nutev.acquire.recoverability import (
    diagnose_recoverability,
    read_metadata_rows,
    recoverability_summary_block,
    unpaywall_is_oa,
    write_recoverability_report,
)

_ROWS = [
    # busca1 guide: PMCID present -> offline OA.
    {"workstream": "busca1", "doi": "10.1/g", "pmid": "", "pmcid": "PMC1", "is_open_access": "", "oa_url": ""},
    # busca2a: is_open_access true -> OA.
    {"workstream": "busca2a", "doi": "10.2/a", "pmid": "111", "pmcid": "", "is_open_access": "true", "oa_url": ""},
    # busca2a: no OA signal, has DOI -> paywall offline.
    {"workstream": "busca2a", "doi": "10.3/b", "pmid": "", "pmcid": "", "is_open_access": "false", "oa_url": ""},
    # busca2b: oa_url present -> OA.
    {"workstream": "busca2b", "doi": "", "pmid": "", "pmcid": "", "is_open_access": "", "oa_url": "http://oa/pdf"},
]


def test_offline_diagnosis_counts_and_percentages():
    d = diagnose_recoverability(_ROWS)
    assert d["online"] is False
    assert d["total"] == 4
    b2a = d["per_workstream"]["busca2a"]
    assert b2a["total"] == 2
    assert b2a["with_doi"] == 2 and b2a["pct_doi"] == 100.0
    assert b2a["open_access"] == 1 and b2a["likely_paywall"] == 1
    # busca1 (PMCID) and busca2b (oa_url) are OA; overall 3/4 OA.
    assert d["overall"]["open_access"] == 3
    assert d["overall"]["pct_open_access"] == 75.0


class _Resp:
    def __init__(self, payload, code=200):
        self._p, self.status_code = payload, code

    def json(self):
        return self._p


class _Session:
    def __init__(self, oa_dois):
        self.oa_dois = oa_dois
        self.calls = 0

    def get(self, url, timeout=None):
        self.calls += 1
        doi = url.split("/v2/")[1].split("?")[0]
        is_oa = doi in self.oa_dois
        return _Resp({"is_oa": is_oa, "best_oa_location": {"url_for_pdf": "x"} if is_oa else None})


def test_online_mode_lifts_oa_via_unpaywall():
    # The only paywall-offline row is busca2a doi 10.3/b; mark it OA in Unpaywall.
    session = _Session(oa_dois={"10.3/b"})
    d = diagnose_recoverability(_ROWS, online=True, email="me@example.org", session=session)
    # Only the offline-paywall DOI row is queried (1 call), and it flips to OA.
    assert session.calls == 1
    assert d["per_workstream"]["busca2a"]["open_access"] == 2
    assert d["overall"]["open_access"] == 4  # all four now OA


def test_online_requires_email_and_session():
    import pytest

    with pytest.raises(ValueError):
        diagnose_recoverability(_ROWS, online=True)


def test_unpaywall_error_is_non_fatal():
    class _Boom:
        def get(self, *a, **k):
            raise OSError("network down")

    cache: dict[str, bool] = {}
    assert unpaywall_is_oa("10.9/x", "me@example.org", _Boom(), cache) is False
    assert cache["10.9/x"] is False  # cached, non-fatal


def test_report_and_summary_block(tmp_path: Path):
    d = diagnose_recoverability(_ROWS)
    out = write_recoverability_report(d, tmp_path / "fulltext_recoverability.csv")
    text = out.read_text(encoding="utf-8-sig")
    assert "workstream" in text and "pct_open_access" in text and "TOTAL" in text
    block = recoverability_summary_block(d)["recoverability"]
    assert block["total"] == 4 and "busca2a" in block["per_workstream_pct_open_access"]


def test_columns_resolved_from_union_not_first_row():
    # Regression: the first row (an official guide) lacks the doi/pmid keys.
    # Column resolution must use the union of keys across all rows, otherwise
    # the whole corpus reports 0 DOIs/PMIDs.
    rows = [
        {"workstream": "busca1", "title": "guide", "pmcid": ""},  # no doi/pmid keys
        {"workstream": "busca2a", "doi": "10.1/x", "pmid": "123", "pmcid": "PMC9"},
        {"workstream": "busca2a", "doi": "10.2/y", "pmid": "456", "pmcid": ""},
    ]
    d = diagnose_recoverability(rows)
    assert d["per_workstream"]["busca2a"]["with_doi"] == 2
    assert d["per_workstream"]["busca2a"]["with_pmid"] == 2


def test_read_metadata_rows_roundtrip(tmp_path: Path):
    p = tmp_path / "article_data.csv"
    p.write_text("workstream,doi,pmcid\nbusca1,10.1/x,PMC9\n", encoding="utf-8")
    rows = read_metadata_rows(p)
    assert rows and rows[0]["workstream"] == "busca1"
