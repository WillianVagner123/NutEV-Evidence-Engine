from __future__ import annotations

from nutev.search.clinicaltrials import (
    _normalize_clinicaltrials,
    search_clinicaltrials,
)

_REQUIRED_KEYS = {
    "source",
    "source_provider",
    "title",
    "abstract",
    "snippet",
    "doi",
    "pmid",
    "pmcid",
    "url",
    "journal",
    "year",
    "publication_date",
    "article_type",
    "authors",
    "metadata_status",
    "query",
    "provider_query",
    "oa_pdf_url",
    "is_open_access",
}

_SAMPLE_STUDY = {
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT01234567",
            "briefTitle": "Mediterranean Diet for Cardiometabolic Health",
        },
        "descriptionModule": {
            "briefSummary": "A randomized trial evaluating the effect of a Mediterranean dietary pattern on cardiometabolic outcomes in adults.",
        },
        "statusModule": {
            "startDateStruct": {"date": "2019-03-01"},
            "studyFirstPostDateStruct": {"date": "2018-11-15"},
        },
        "designModule": {"studyType": "INTERVENTIONAL"},
        "sponsorCollaboratorsModule": {
            "leadSponsor": {"name": "National Heart, Lung, and Blood Institute"},
        },
        "conditionsModule": {"conditions": ["Type 2 Diabetes", "Hypertension"]},
    }
}


def test_normalize_clinicaltrials_maps_fields():
    row = _normalize_clinicaltrials(_SAMPLE_STUDY, "mediterranean diet")

    assert _REQUIRED_KEYS.issubset(row.keys())
    assert set(row.keys()) == _REQUIRED_KEYS

    assert row["source"] == "clinicaltrials"
    assert row["source_provider"] == "clinicaltrials"
    assert row["title"] == "Mediterranean Diet for Cardiometabolic Health"
    assert "Mediterranean dietary pattern" in row["abstract"]
    assert row["article_type"] == "INTERVENTIONAL"
    assert row["year"] == "2019"
    assert row["authors"] == "National Heart, Lung, and Blood Institute"
    assert row["journal"] == "ClinicalTrials.gov"
    assert row["is_open_access"] == "true"
    assert row["oa_pdf_url"] == ""
    assert row["query"] == "mediterranean diet"
    assert row["provider_query"] == "mediterranean diet"

    # url must contain the NCT id
    assert "NCT01234567" in row["url"]
    assert row["url"] == "https://clinicaltrials.gov/study/NCT01234567"

    # conditions appended to abstract context
    assert "Type 2 Diabetes" in row["abstract"]

    # snippet derived from brief summary, truncated
    assert row["snippet"]
    assert len(row["snippet"]) <= 300
    assert row["snippet"] in row["abstract"]


def test_normalize_clinicaltrials_missing_fields_default_empty():
    row = _normalize_clinicaltrials({}, "q")

    assert set(row.keys()) == _REQUIRED_KEYS
    assert row["title"] == ""
    assert row["abstract"] == ""
    assert row["snippet"] == ""
    assert row["url"] == ""
    assert row["year"] == ""
    assert row["authors"] == ""
    assert row["journal"] == "ClinicalTrials.gov"
    assert row["query"] == "q"


def test_normalize_clinicaltrials_year_falls_back_to_first_post_date():
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT99999999", "briefTitle": "T"},
            "statusModule": {"studyFirstPostDateStruct": {"date": "2021-06-10"}},
        }
    }
    row = _normalize_clinicaltrials(study, "q")
    assert row["year"] == "2021"
    assert row["publication_date"] == "2021-06-10"


def test_search_returns_empty_when_network_disabled(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")

    def _boom(*args, **kwargs):  # pragma: no cover - must never be called
        raise AssertionError("network must not be used when disabled")

    monkeypatch.setattr("requests.get", _boom)

    assert search_clinicaltrials("anything", limit=5) == []
