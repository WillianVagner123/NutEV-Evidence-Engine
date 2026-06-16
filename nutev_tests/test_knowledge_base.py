from __future__ import annotations

import json

from nutev.export.knowledge_base import (
    load_kb_records_from_metadata_csv,
    to_kb_record,
    to_kb_records,
    write_knowledge_base,
)
from nutev.export.metadata_tables import write_metadata_csv


def test_to_kb_record_coerces_and_maps():
    row = {
        "document_id": "doc1",
        "workstream": "busca2b",
        "title": "Mediterranean diet and T2D",
        "abstract": "RCT",
        "year": "2021",
        "language": "en",
        "countries": ["BR", "US"],
        "region": "South America",
        "journal": "Nutrients",
        "issn": "2072-6643",
        "publisher": "MDPI",
        "doi": "10.1/x",
        "url": "http://landing",
        "final_url": "http://pdf",
        "matched_providers": ["openalex", "pubmed"],
        "domains": ["dietary_pattern"],
        "outcomes": ["glycemic_control"],
        "diet_patterns": "mediterranean;dash",
        "clinical_conditions": "['diabetes', 'obesity']",
        "article_type": "article",
        "editorial_priority_tier": "a1_proxy_high",
        "relevance_score": 42,
        "cited_by_count": "9",
    }
    rec = to_kb_record(row)
    assert rec["document_id"] == "doc1"
    assert rec["year"] == 2021
    assert rec["url"] == "http://pdf"  # final_url preferred
    assert rec["countries"] == ["BR", "US"]
    assert rec["source_providers"] == ["openalex", "pubmed"]
    assert rec["diet_patterns"] == ["mediterranean", "dash"]
    assert rec["clinical_conditions"] == ["diabetes", "obesity"]  # list-repr parsed
    assert rec["evidence_type"] == "article"
    assert rec["evidence_tier"] == "a1_proxy_high"
    assert rec["cited_by_count"] == 9


def test_to_kb_records_drops_idless_and_writes_files(tmp_path):
    rows = [
        {"doi": "10.1/a", "title": "A", "countries": ["BR"], "domains": ["d1"]},
        {"title": "", "abstract": ""},  # no id-able field -> dropped
    ]
    records = to_kb_records(rows)
    assert len(records) == 1
    paths = write_knowledge_base(records, tmp_path)
    # jsonl: one record per line, valid json
    lines = (tmp_path / "corpus.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["document_id"] == "10.1/a"
    # csv + schema + data dictionary present
    assert paths["corpus_csv"].exists()
    schema = json.loads((tmp_path / "schema.json").read_text(encoding="utf-8"))
    assert any(f["name"] == "countries" for f in schema["fields"])
    assert (tmp_path / "data_dictionary.md").exists()


def test_metadata_csv_roundtrip_rebuilds_kb(tmp_path):
    rows = [{
        "document_id": "doc9",
        "title": "Plant-based diet",
        "countries": ["PT", "ES"],
        "domains": ["dietary_pattern"],
        "year": 2020,
        "journal": "Foods",
    }]
    csv_path = tmp_path / "metadata_master.csv"
    write_metadata_csv(rows, csv_path)
    records = load_kb_records_from_metadata_csv(csv_path)
    assert len(records) == 1
    rec = records[0]
    assert rec["countries"] == ["PT", "ES"]  # ;-joined in CSV -> list
    assert rec["domains"] == ["dietary_pattern"]  # list-repr in CSV -> list
    assert rec["year"] == 2020


def test_load_missing_csv_returns_empty(tmp_path):
    assert load_kb_records_from_metadata_csv(tmp_path / "nope.csv") == []
