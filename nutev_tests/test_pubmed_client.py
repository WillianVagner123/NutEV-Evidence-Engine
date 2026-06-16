from __future__ import annotations

import json

from nutev.search.pubmed import (
    PubMedClient,
    _details_from_efetch_xml,
    _normalize_summary,
)

_EFETCH_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>123</PMID>
      <Article>
        <Language>eng</Language>
        <Abstract>
          <AbstractText>Background text.</AbstractText>
          <AbstractText>Conclusion text.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Silva</LastName>
            <AffiliationInfo>
              <Affiliation>Universidade de Sao Paulo, Sao Paulo, Brazil.</Affiliation>
            </AffiliationInfo>
          </Author>
          <Author>
            <LastName>Smith</LastName>
            <AffiliationInfo>
              <Affiliation>University of Oxford, Oxford, United Kingdom.</Affiliation>
            </AffiliationInfo>
          </Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


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


def test_normalize_summary_has_uniform_affiliations_and_language():
    row = _normalize_summary({"title": "T", "lang": ["eng"]}, "1", "q")
    assert row["affiliations"] == []  # esummary carries no affiliations
    assert row["language"] == "eng"
    # esummary with no language reports an empty string (uniform shape).
    assert _normalize_summary({"title": "T"}, "1", "q")["language"] == ""


def test_details_from_efetch_xml_parses_affiliations_and_language():
    details = _details_from_efetch_xml(_EFETCH_XML)
    assert set(details) == {"123"}
    entry = details["123"]
    assert entry["language"] == "eng"
    assert entry["affiliations"] == [
        "Universidade de Sao Paulo, Sao Paulo, Brazil.",
        "University of Oxford, Oxford, United Kingdom.",
    ]
    assert "Background text." in entry["abstract"]
    assert "Conclusion text." in entry["abstract"]


def test_pubmed_efetch_populates_affiliations_and_language(monkeypatch, tmp_path):
    def fake_request(endpoint, params, **kwargs):
        if endpoint == "esearch.fcgi" and params.get("retmax") == 0:
            return {"esearchresult": {"count": "1", "webenv": "WE", "querykey": "1"}}
        if endpoint == "esearch.fcgi":
            return {"esearchresult": {"idlist": ["123"]}}
        return {"result": {"123": {"title": "Nutrition trial", "pubdate": "2024"}}}

    monkeypatch.setenv("NUTEV_PUBMED_FETCH_ABSTRACTS", "1")
    monkeypatch.setattr("nutev.search.pubmed._request_json", fake_request)
    monkeypatch.setattr("nutev.search.pubmed._request_text", lambda *a, **k: _EFETCH_XML)
    result = PubMedClient().search("nutrition", limit=1, context={"checkpoint_dir": tmp_path, "workstream": "busca1"})
    assert result.status == "completed"
    row = result.rows[0]
    assert row["affiliations"] == [
        "Universidade de Sao Paulo, Sao Paulo, Brazil.",
        "University of Oxford, Oxford, United Kingdom.",
    ]
    assert row["language"] == "eng"
    assert row["metadata_status"] == "pubmed_efetch"
