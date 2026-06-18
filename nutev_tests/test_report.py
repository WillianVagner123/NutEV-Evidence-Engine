from __future__ import annotations

import json

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
    ]
    (kb / "corpus.jsonl").write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    tables = root / "06_tables"
    tables.mkdir()
    import csv
    with (tables / "NUTEV_EVIDENCE_CLAIMS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["document_id", "title", "year", "claim_text", "exact_quote", "source_url", "nutev_domains", "claim_status"])
        w.writerow(["doc1", "Mediterranean diet and obesity", "2021", "MedDiet reduces weight", "...lost 3kg...", "http://x", "dietary_patterns", "supported"])
    logs = root / "07_logs"
    logs.mkdir()
    (logs / "run_summary.json").write_text(json.dumps({
        "records": 2, "curated_unique_documents": 2, "evidence_claims_total": 5,
        "evidence_claims_supported": 3, "evidence_claims_needs_review": 2,
        "recommendation_candidates_total": 1, "conflicting_evidence_total": 0, "workstreams": ["busca1"],
    }), encoding="utf-8")


def test_build_dissertation_report(tmp_path):
    _seed_run(tmp_path)
    res = build_dissertation_report(tmp_path)
    assert res["available"] and res["n_documents"] == 2
    rep = tmp_path / "09_report"
    for name in ("INDICE.md", "referencias.bib", "referencias.ris", "estudos_incluidos.csv",
                 "NUTEV_DISSERTACAO.xlsx", "RELATORIO_DISSERTACAO.md", "RESUMO_EXECUTIVO.md"):
        assert (rep / name).exists(), name
    import openpyxl
    sheets = openpyxl.load_workbook(rep / "NUTEV_DISSERTACAO.xlsx").sheetnames
    assert "Estudos_incluidos" in sheets and "Por_tema" in sheets and "Principais_achados" in sheets
    # every study row carries a citation key that matches a .bib entry
    studies_csv = (rep / "estudos_incluidos.csv").read_text(encoding="utf-8")
    assert "chave_citacao" in studies_csv
    # findings linked to article + citation key + DOI
    achados = (rep / "achados_principais.csv").read_text(encoding="utf-8")
    assert "MedDiet reduces weight" in achados and "chave_citacao" in achados and "10.1/x" in achados
    bib = (rep / "referencias.bib").read_text(encoding="utf-8")
    assert "Mediterranean diet and obesity" in bib and "Silva" in bib
    ris = (rep / "referencias.ris").read_text(encoding="utf-8")
    assert "TY  - JOUR" in ris and "AU  - Silva J" in ris
    rel = (rep / "RELATORIO_DISSERTACAO.md").read_text(encoding="utf-8")
    assert "Avaliação dos artigos" in rel and "revisão humana" in rel
    # the included-studies table carries the per-article evaluation columns
    studies = (rep / "estudos_incluidos.csv").read_text(encoding="utf-8")
    assert "qualidade_periodico" in studies and "Nutrients" in studies


def test_build_dissertation_report_no_run(tmp_path):
    res = build_dissertation_report(tmp_path)
    assert res["available"] is False


def test_report_route_without_run(tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from nutev.api.server import create_app

    client = TestClient(create_app(tmp_path))
    assert client.post("/api/report").json()["available"] is False
