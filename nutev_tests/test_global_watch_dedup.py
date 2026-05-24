from __future__ import annotations

from nutev.global_watch.watch_pipeline import _dedup_watch_rows, normalize_watch_hit


def test_dedup_watch_rows_merges_metadata_and_affinity() -> None:
    rows = [
        {
            "document_id": "doc_same",
            "title": "Lifestyle nutrition guidance",
            "abstract": "",
            "snippet": "",
            "url": "https://doi.org/10.1000/example",
            "doi": "",
            "year": 2025,
            "source_provider": "crossref",
            "category": "guidelines_consensus",
            "query": "guideline",
            "evidence_type": "guideline",
            "workstream_affinity": ["busca1"],
            "download_status": "metadata_only",
            "relevance_score": 50,
            "failure_reason": "",
            "fallback_used": False,
            "is_recent_publication": True,
        },
        {
            "document_id": "doc_same",
            "title": "Lifestyle nutrition guidance",
            "abstract": "Implementation fidelity and food literacy support for obesity care.",
            "snippet": "Teaching kitchens and dietary adherence.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/123456/",
            "doi": "10.1000/example",
            "year": 2025,
            "source_provider": "pubmed",
            "category": "implementation_behavior",
            "query": "implementation",
            "evidence_type": "guideline",
            "workstream_affinity": ["busca2b", "a3"],
            "download_status": "metadata_only",
            "relevance_score": 50,
            "failure_reason": "",
            "fallback_used": False,
            "is_recent_publication": True,
        },
    ]

    merged = _dedup_watch_rows(rows)

    assert len(merged) == 1
    row = merged[0]
    assert row["source_provider"] == "pubmed"
    assert row["doi"] == "10.1000/example"
    assert row["abstract"] == "Implementation fidelity and food literacy support for obesity care."
    assert row["workstream_affinity"] == ["busca1", "busca2b", "a3"]
    assert row["matched_categories"] == "guidelines_consensus|implementation_behavior"
    assert row["matched_providers"] == "crossref|pubmed"


def test_dedup_watch_rows_keeps_stronger_download_status() -> None:
    rows = [
        {
            "document_id": "doc_capture",
            "title": "Nutrition trial",
            "url": "https://example.org/landing",
            "source_provider": "openalex",
            "category": "implementation_behavior",
            "query": "trial",
            "evidence_type": "trial",
            "workstream_affinity": ["busca2b"],
            "download_status": "metadata_only",
            "relevance_score": 50,
            "failure_reason": "",
            "fallback_used": False,
            "is_recent_publication": False,
        },
        {
            "document_id": "doc_capture",
            "title": "Nutrition trial",
            "url": "https://example.org/fulltext.pdf",
            "source_provider": "crossref",
            "category": "implementation_behavior",
            "query": "trial",
            "evidence_type": "trial",
            "workstream_affinity": ["busca2b"],
            "download_status": "pdf",
            "relevance_score": 50,
            "failure_reason": "",
            "fallback_used": False,
            "is_recent_publication": True,
        },
    ]

    merged = _dedup_watch_rows(rows)

    assert len(merged) == 1
    row = merged[0]
    assert row["download_status"] == "pdf"
    assert row["url"] == "https://example.org/fulltext.pdf"
    assert row["is_recent_publication"] is True


def test_normalize_watch_hit_uses_abstract_and_snippet_for_workstream_affinity() -> None:
    item = normalize_watch_hit(
        {
            "title": "Nutrition update",
            "abstract": "Implementation fidelity for obesity care.",
            "summary": "Food literacy and teaching kitchens for dietary adherence.",
            "url": "https://example.org/article",
            "year": 2025,
        },
        "pubmed",
        "implementation_behavior",
        "nutrition update",
    )

    assert "busca2b" in item["workstream_affinity"]
    assert "a3" in item["workstream_affinity"]
    assert item["matched_categories"] == "implementation_behavior"
    assert item["matched_providers"] == "pubmed"


def test_normalize_watch_hit_maps_produce_rx_variants_to_busca2b() -> None:
    item = normalize_watch_hit(
        {
            "title": "Produce Rx and healthy food prescription program for hypertension management",
            "abstract": "Fruit and vegetable prescription delivery in a cardiometabolic nutrition clinic.",
            "url": "https://example.org/produce-rx",
            "year": 2025,
        },
        "pubmed",
        "lifestyle_medicine",
        "produce rx hypertension",
    )

    assert "busca2b" in item["workstream_affinity"]
    assert "busca2a" in item["workstream_affinity"]
