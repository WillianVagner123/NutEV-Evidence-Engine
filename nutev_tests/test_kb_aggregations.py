"""Tests for ``nutev.export.kb_aggregations``."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from nutev.export.kb_aggregations import _top, write_aggregations


def _records() -> list[dict]:
    """Synthetic knowledge base records covering the interesting edge cases."""
    return [
        {
            "document_id": "doc-1",
            "workstream": "ws-a",
            "title": "Mediterranean diet and cardiometabolic risk",
            "abstract": "A study.",
            "authors": "Silva J",
            "year": 2021,
            "language": "en",
            "countries": ["BR", "US"],  # multi-country doc
            "region": "Americas",
            "journal": "Journal of Nutrition",
            "issn": "1234-5678",
            "publisher": "Elsevier",
            "doi": "10.1/a",
            "url": "https://example.org/a",
            "source_providers": ["openalex", "pubmed"],
            "domains": ["nutrition", "cardiology"],
            "outcomes": ["weight_loss"],
            "diet_patterns": ["mediterranean"],
            "clinical_conditions": ["obesity"],
            "evidence_type": "rct",
            "evidence_tier": "tier1",
            "relevance_score": 0.9,
            "cited_by_count": 12,
        },
        {
            "document_id": "doc-2",
            "workstream": "ws-a",
            "title": "Dieta e saude no Brasil",
            "abstract": "Um estudo.",
            "authors": "Souza A",
            "year": 2021,
            "language": "pt",
            "countries": ["BR"],
            "region": "South America",
            "journal": "Revista Brasileira",
            "issn": "2222-3333",
            "publisher": "SciELO",
            "doi": "10.1/b",
            "url": "https://example.org/b",
            "source_providers": ["openalex"],
            "domains": ["nutrition"],
            "outcomes": ["diabetes_control"],
            "diet_patterns": ["dash"],
            "clinical_conditions": ["diabetes"],
            "evidence_type": "cohort",
            "evidence_tier": "tier2",
            "relevance_score": 7,
            "cited_by_count": 3,
        },
        {
            "document_id": "doc-3",
            "workstream": "ws-b",
            "title": "Plant based diets in China",
            "abstract": "A study.",
            "authors": "Li W",
            "year": 2019,
            "language": "zh",
            "countries": ["CN"],
            "region": "Asia",
            "journal": "Journal of Nutrition",  # shared venue with doc-1
            "issn": "1234-5678",
            "publisher": "Elsevier",
            "doi": "10.1/c",
            "url": "https://example.org/c",
            "source_providers": ["pubmed"],
            "domains": ["nutrition"],
            "outcomes": ["weight_loss"],
            "diet_patterns": ["plant_based"],
            "clinical_conditions": [],
            "evidence_type": "review",
            "evidence_tier": "tier2",
            "relevance_score": 5,
            "cited_by_count": 30,
        },
        {
            # empty-countries doc -> must land under UNKNOWN; messy/missing types
            "document_id": "doc-4",
            "workstream": "ws-b",
            "title": "Global review",
            "abstract": "",
            "authors": "",
            "year": "2023",  # string year -> coerced to int
            "language": "",  # unknown language
            "countries": [],
            "region": "",
            "journal": "Global Health Review",
            "issn": "",
            "publisher": "",
            "doi": "",
            "url": "",
            "source_providers": [],
            "domains": ["policy"],
            "outcomes": [],
            "diet_patterns": [],
            "clinical_conditions": [],
            "evidence_type": "review",
            "evidence_tier": "tier3",
            "relevance_score": 1,
            "cited_by_count": 0,
        },
        {
            # heavily malformed record: missing fields / wrong types everywhere
            "document_id": "doc-5",
            "title": "Broken record",
            "year": None,  # no year -> skipped from by_year
            "language": "en",
            "countries": None,  # None -> UNKNOWN
            "journal": "",  # empty journal -> excluded from by_venue
            "domains": None,
            "outcomes": "single_outcome_as_string",  # scalar -> wrapped
            "diet_patterns": None,
            "clinical_conditions": None,
            "source_providers": None,
        },
    ]


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_top_helper_orders_and_breaks_ties() -> None:
    counter = Counter({"b": 2, "a": 2, "c": 1, "": 99})
    # ties broken alphabetically, empty term skipped, "term(count)" format
    assert _top(counter, n=2) == "a(2);b(2)"
    assert _top(counter, n=1) == "a(2)"


def test_files_created(tmp_path: Path) -> None:
    paths = write_aggregations(_records(), tmp_path)
    expected = {
        "by_country",
        "by_venue",
        "by_language",
        "by_year",
        "by_concept",
        "overview",
    }
    assert set(paths) == expected
    for name, path in paths.items():
        assert path.exists(), name
        assert path.stat().st_size > 0, name


def test_multi_country_doc_counts_in_both(tmp_path: Path) -> None:
    write_aggregations(_records(), tmp_path)
    rows = {r["country"]: r for r in _read_csv(tmp_path / "by_country.csv")}

    # doc-1 is ["BR","US"]; doc-2 is ["BR"] -> BR has 2 docs, US has 1.
    assert "BR" in rows
    assert "US" in rows
    assert int(rows["BR"]["n_docs"]) == 2
    assert int(rows["US"]["n_docs"]) == 1
    # US only comes from doc-1 (mediterranean / obesity)
    assert "mediterranean" in rows["US"]["top_diet_patterns"]


def test_empty_countries_doc_under_unknown(tmp_path: Path) -> None:
    write_aggregations(_records(), tmp_path)
    rows = {r["country"]: r for r in _read_csv(tmp_path / "by_country.csv")}
    assert "UNKNOWN" in rows
    assert "" not in rows  # the empty sentinel must be rendered as UNKNOWN
    # doc-4 (policy) and doc-5 (broken, None countries) -> 2 unknown docs
    assert int(rows["UNKNOWN"]["n_docs"]) == 2
    assert "policy" in rows["UNKNOWN"]["top_domains"]


def test_by_venue(tmp_path: Path) -> None:
    write_aggregations(_records(), tmp_path)
    rows = {r["journal"]: r for r in _read_csv(tmp_path / "by_venue.csv")}
    # empty-journal records must not appear
    assert "" not in rows
    # "Journal of Nutrition" shared by doc-1 and doc-3
    jon = rows["Journal of Nutrition"]
    assert int(jon["n_docs"]) == 2
    assert jon["issn"] == "1234-5678"
    assert jon["publisher"] == "Elsevier"
    # most common single country for that venue: BR, US, CN each once -> BR (alpha)
    assert jon["country"] == "BR"


def test_by_language(tmp_path: Path) -> None:
    write_aggregations(_records(), tmp_path)
    rows = {r["language"]: r for r in _read_csv(tmp_path / "by_language.csv")}
    # doc-1 (en) + doc-5 (en) -> en has 2
    assert int(rows["en"]["n_docs"]) == 2
    assert int(rows["pt"]["n_docs"]) == 1
    assert int(rows["zh"]["n_docs"]) == 1
    # empty language rendered as "unknown" (doc-4)
    assert "unknown" in rows
    assert int(rows["unknown"]["n_docs"]) == 1


def test_by_year(tmp_path: Path) -> None:
    write_aggregations(_records(), tmp_path)
    rows = _read_csv(tmp_path / "by_year.csv")
    years = [r["year"] for r in rows]
    # None year (doc-5) skipped; remaining sorted ascending
    assert years == ["2019", "2021", "2023"]
    by_year = {r["year"]: int(r["n_docs"]) for r in rows}
    assert by_year["2021"] == 2  # doc-1 + doc-2


def test_by_concept_has_rows_for_domains(tmp_path: Path) -> None:
    write_aggregations(_records(), tmp_path)
    rows = _read_csv(tmp_path / "by_concept.csv")
    domains_present = {
        r["concept"] for r in rows if r["concept_type"] == "domain"
    }
    # every domain across the corpus should have a row
    assert {"nutrition", "cardiology", "policy"} <= domains_present

    # nutrition appears in doc-1, doc-2, doc-3 -> 3 docs
    nutrition = next(
        r
        for r in rows
        if r["concept_type"] == "domain" and r["concept"] == "nutrition"
    )
    assert int(nutrition["n_docs"]) == 3

    # concept_type column is sorted ascending
    types = [r["concept_type"] for r in rows]
    assert types == sorted(types)

    # scalar outcome on doc-5 was wrapped into a single-element list
    outcomes_present = {
        r["concept"] for r in rows if r["concept_type"] == "outcome"
    }
    assert "single_outcome_as_string" in outcomes_present


def test_overview_totals(tmp_path: Path) -> None:
    records = _records()
    write_aggregations(records, tmp_path)
    overview = json.loads((tmp_path / "overview.json").read_text("utf-8"))

    assert overview["n_documents"] == len(records)
    # distinct real countries: BR, US, CN
    assert overview["n_countries"] == 3
    # distinct non-empty journals: Journal of Nutrition, Revista Brasileira,
    # Global Health Review
    assert overview["n_journals"] == 3
    assert overview["year_min"] == 2019
    assert overview["year_max"] == 2023
    # providers tallied across records
    assert overview["providers"]["openalex"] == 2
    assert overview["providers"]["pubmed"] == 2
    # top_countries is a list of [code, count] pairs, BR leads with 2
    assert overview["top_countries"][0] == ["BR", 2]


def test_deterministic_same_bytes(tmp_path: Path) -> None:
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    paths_a = write_aggregations(_records(), out_a)
    paths_b = write_aggregations(_records(), out_b)
    assert set(paths_a) == set(paths_b)
    for name in paths_a:
        assert (
            paths_a[name].read_bytes() == paths_b[name].read_bytes()
        ), name

    # re-running into the SAME directory is also stable
    before = {n: p.read_bytes() for n, p in paths_a.items()}
    write_aggregations(_records(), out_a)
    for name, prev in before.items():
        assert paths_a[name].read_bytes() == prev, name


def test_empty_input(tmp_path: Path) -> None:
    paths = write_aggregations([], tmp_path)
    assert len(paths) == 6
    overview = json.loads((tmp_path / "overview.json").read_text("utf-8"))
    assert overview["n_documents"] == 0
    assert overview["year_min"] is None
    assert overview["year_max"] is None
