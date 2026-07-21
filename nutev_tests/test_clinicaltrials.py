"""ClinicalTrials.gov v2 connector: normalization + reproducible default + cursor pagination."""
from __future__ import annotations

import nutev.search.clinicaltrials as ct


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _study(nct, title, summary="A trial.", start="2026-02", sponsor="Univ X"):
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct, "briefTitle": title},
            "descriptionModule": {"briefSummary": summary},
            "statusModule": {"startDateStruct": {"date": start}},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": sponsor}},
        }
    }


def _page(studies, next_token=None):
    out = {"studies": studies}
    if next_token:
        out["nextPageToken"] = next_token
    return out


def test_normalizes_a_study(monkeypatch):
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(ct.requests, "get", lambda *a, **k: _Resp(_page([_study("NCT01", "Diet trial in obesity")])))
    r = ct.search_clinicaltrials("diet")[0]
    assert r["source_provider"] == "clinicaltrials"
    assert r["title"] == "Diet trial in obesity"
    assert r["registry_id"] == "NCT01"
    assert r["url"] == "https://clinicaltrials.gov/study/NCT01"
    assert r["year"] == "2026"
    assert r["article_type"] == "clinical_trial"
    assert r["source_institution"] == "Univ X"
    assert r["doi"] == ""  # trials have no DOI


def test_default_single_page_no_token(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None, headers=None):
        calls.append(params)
        return _Resp(_page([_study("NCT01", "A")], next_token="tok"))

    monkeypatch.delenv("NUTEV_CLINICALTRIALS_MAX_RESULTS", raising=False)
    monkeypatch.setattr(ct.requests, "get", fake_get)
    rows = ct.search_clinicaltrials("diet", page_size=18)
    assert len(calls) == 1 and "pageToken" not in calls[0]
    assert len(rows) == 1


def test_cursor_pagination_and_dedup(monkeypatch):
    pages = [
        _page([_study("NCT01", "A"), _study("NCT02", "B")], next_token="t2"),
        _page([_study("NCT02", "B-dup"), _study("NCT03", "C")], next_token="t3"),
    ]
    seq = iter(pages)
    monkeypatch.setattr(ct.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = ct.search_clinicaltrials("diet", page_size=2, max_results=3)
    assert [r["registry_id"] for r in rows] == ["NCT01", "NCT02", "NCT03"]


def test_stops_when_no_next_token(monkeypatch):
    seq = iter([_page([_study("NCT01", "A")])])  # no nextPageToken
    monkeypatch.setattr(ct.requests, "get", lambda *a, **k: _Resp(next(seq)))
    rows = ct.search_clinicaltrials("diet", page_size=5, max_results=50)
    assert [r["registry_id"] for r in rows] == ["NCT01"]


def test_network_disabled_and_skip(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert ct.search_clinicaltrials("q") == []
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK")
    monkeypatch.setenv("NUTEV_SKIP_CLINICALTRIALS", "1")
    assert ct.search_clinicaltrials("q") == []
