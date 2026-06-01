from __future__ import annotations

import json

from nutev.search.pubmed import PubMedClient


def test_pubmed_uses_history_and_returns_row(monkeypatch, tmp_path):
    calls = []

    def fake_request(endpoint, params, **kwargs):
        calls.append((endpoint, dict(params)))
        if endpoint == "esearch.fcgi" and params.get("retmax") == 0:
            return {"esearchresult": {"count": "1", "webenv": "WE", "querykey": "1"}}
        if endpoint == "esearch.fcgi":
            return {"esearchresult": {"idlist": ["123"]}}
        return {"result": {"123": {"title": "Nutrition trial", "articleids": [{"idtype": "doi", "value": "doi:10.1000/test"}, {"idtype": "pmc", "value": "PMC12345"}], "pubdate": "2024", "authors": [{"name": "A Author"}]}}}

    monkeypatch.setattr("nutev.search.pubmed._request_json", fake_request)
    result = PubMedClient().search("nutrition", limit=1, context={"checkpoint_dir": tmp_path, "workstream": "busca1"})
    assert result.status == "completed"
    assert result.rows[0]["pmid"] == "123"
    assert result.rows[0]["doi"] == "10.1000/test"
    assert result.rows[0]["url"].startswith("https://pmc.ncbi.nlm.nih.gov")
    assert calls[0][1]["usehistory"] == "y"
    assert any(call[1].get("WebEnv") == "WE" and call[1].get("query_key") == "1" for call in calls)


def test_pubmed_pagination_checkpoint_resume(monkeypatch, tmp_path):
    def fake_request(endpoint, params, **kwargs):
        if endpoint == "esearch.fcgi" and params.get("retmax") == 0:
            return {"esearchresult": {"count": "450", "webenv": "WE", "querykey": "1"}}
        if endpoint == "esearch.fcgi":
            start = int(params["retstart"])
            size = int(params["retmax"])
            return {"esearchresult": {"idlist": [str(i) for i in range(start + 1, start + size + 1)]}}
        ids = str(params["id"]).split(",")
        return {"result": {pmid: {"title": f"Title {pmid}", "pubdate": "2025"} for pmid in ids}}

    monkeypatch.setattr("nutev.search.pubmed._request_json", fake_request)
    result = PubMedClient().search("x", limit=450, context={"checkpoint_dir": tmp_path, "workstream": "busca1", "batch_size": 200})
    assert len(result.rows) == 450
    checkpoint = next((tmp_path / "pubmed").glob("*.json"))
    data = json.loads(checkpoint.read_text())
    assert data["retstart_done"] == 450
    resumed = PubMedClient().search("x", limit=450, context={"checkpoint_dir": tmp_path, "workstream": "busca1", "resume": True})
    assert len({row["pmid"] for row in resumed.rows}) == 450


def test_pubmed_failure_returns_failed(monkeypatch, tmp_path):
    monkeypatch.setattr("nutev.search.pubmed._request_json", lambda *a, **k: (_ for _ in ()).throw(ValueError("bad json")))
    result = PubMedClient().search("x", limit=1, context={"checkpoint_dir": tmp_path, "workstream": "busca1"})
    assert result.status == "failed"
    assert result.rows == []
    assert "bad json" in result.error
