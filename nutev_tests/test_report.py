from __future__ import annotations

import csv
import json
import re

import pytest

from nutev.export.report import build_dissertation_report


def _seed_run(root):
    kb = root / "11_knowledge_base"
    kb.mkdir(parents=True)
    records = [
        {"document_id": "doc1", "title": "Mediterranean diet and obesity", "authors": "Silva J; Souza M", "year": "2021", "journal": "Nutrients",
         "doi": "10.1/x", "url": "http://x", "countries": "['Brazil']", "domains": "['dietary_patterns']",
         "evidence_tier": "a1_proxy_high", "evidence_type": "rct", "journal_quality_score": "0.8",
         "cited_by_count": "42", "relevance_score": "9", "workstream": "busca1"},
        {"document_id": "doc2", "title": "Plant-based patterns", "authors": "", "year": "", "journal": "", "doi": "", "url": "http://y",
         "countries": "[]", "domains": "[]", "evidence_tier": "", "evidence_type": "", "journal_quality_score": "",
         "cited_by_count": "3", "relevance_score": "1", "workstream": "busca1"},
        {"document_id": "doc3", "title": "Vitamin C & D in 50%_of cases", "authors": "Mozaffarian D", "year": "2020", "journal": "J & Health",
         "doi": "10.2/z", "url": "http://z", "countries": "['USA']", "domains": "['micronutrients']",
         "evidence_tier": "a1_proxy_high", "evidence_type": "review", "journal_quality_score": "0.6",
         "cited_by_count": "10", "relevance_score": "5", "workstream": "busca1"},
    ]
    (kb / "corpus.jsonl").write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    tables = root / "06_tables"
    tables.mkdir()
    with (tables / "NUTEV_EVIDENCE_CLAIMS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["document_id", "title", "year", "claim_text", "exact_quote", "source_url", "nutev_domains", "claim_status"])
        w.writerow(["doc1", "Mediterranean diet and obesity", "2021", "MedDiet reduces weight", "...lost 3kg...", "http://x", "['dietary_patterns', 'obesity']", "supported"])
        w.writerow(["doc3", "Vitamin C & D", "", "Vit D helps", "...", "http://z", "['micronutrients']", "supported"])  # blank year -> pandas float64
    (root / "07_logs").mkdir()
    (root / "07_logs" / "run_summary.json").write_text(json.dumps({
        "records": 3, "curated_unique_documents": 3, "evidence_claims_total": 2,
        "evidence_claims_supported": 2, "evidence_claims_needs_review": 0,
        "recommendation_candidates_total": 0, "conflicting_evidence_total": 0, "workstreams": ["busca1"],
    }), encoding="utf-8")


def test_build_dissertation_report(tmp_path):
    _seed_run(tmp_path)
    res = build_dissertation_report(tmp_path)
    assert res["available"] and res["n_documents"] == 3
    rep = tmp_path / "09_report"
    for name in ("INDICE.md", "referencias.bib", "referencias.ris", "estudos_incluidos.csv",
                 "achados_principais.csv", "NUTEV_DISSERTACAO.xlsx", "RELATORIO_DISSERTACAO.md", "RESUMO_EXECUTIVO.md"):
        assert (rep / name).exists(), name
    import openpyxl
    sheets = openpyxl.load_workbook(rep / "NUTEV_DISSERTACAO.xlsx").sheetnames
    assert "Estudos_incluidos" in sheets and "Por_tema" in sheets and "Principais_achados" in sheets

    achados = (rep / "achados_principais.csv").read_text(encoding="utf-8")
    assert "MedDiet reduces weight" in achados and "10.1/x" in achados
    assert "dietary_patterns; obesity" in achados and "['" not in achados  # tema cleaned, no list-repr
    assert ".0" not in achados  # year normalized (no 2021.0)


def test_bibtex_escaping_and_clean(tmp_path):
    _seed_run(tmp_path)
    build_dissertation_report(tmp_path)
    bib = (tmp_path / "09_report" / "referencias.bib").read_text(encoding="utf-8")
    # LaTeX special chars escaped in field values
    assert r"\&" in bib and r"\%" in bib and r"\_" in bib
    assert "Mozaffarian2020" in bib  # surname (not initial) + year


def test_citation_keys_unique_and_valid(tmp_path):
    kb = tmp_path / "11_knowledge_base"
    kb.mkdir(parents=True)
    # 40 documents with NO authors/year -> all share the same base key
    records = [{"document_id": f"d{i}", "title": f"Doc {i}", "authors": "", "year": "", "url": f"http://x/{i}"} for i in range(40)]
    (kb / "corpus.jsonl").write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    build_dissertation_report(tmp_path)
    bib = (tmp_path / "09_report" / "referencias.bib").read_text(encoding="utf-8")
    keys = re.findall(r"@article\{([^,]+),", bib)
    assert len(keys) == 40
    assert len(set(keys)) == 40  # unique
    assert all(re.fullmatch(r"[A-Za-z0-9]+", k) for k in keys)  # valid BibTeX keys, no { | } ~


def test_build_dissertation_report_no_run(tmp_path):
    assert build_dissertation_report(tmp_path)["available"] is False


def test_report_route_without_run(tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from nutev.api.server import create_app

    client = TestClient(create_app(tmp_path))
    assert client.post("/api/report").json()["available"] is False
