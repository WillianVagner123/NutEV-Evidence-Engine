from __future__ import annotations

import csv
from pathlib import Path

from nutev.export.audit_artifacts import write_audit_and_convergence, write_audit_artifacts


def _rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_write_audit_artifacts_creates_expected_csvs(tmp_path: Path):
    rows = [
        {
            "document_id": "doc_1",
            "title": "Clinical guideline should encourage vegetables for obesity care.",
            "abstract": "The guideline should encourage vegetables for adults with obesity.",
            "extracted_text": "The guideline should encourage vegetables for adults with obesity.",
            "source_provider": "demo",
            "source_type": "clinical_guideline",
            "clinical_conditions": ["obesity"],
            "diet_patterns": ["plant_forward"],
            "outcomes": ["weight_management"],
        }
    ]

    summary = write_audit_artifacts(rows, tmp_path)

    assert (tmp_path / "NUTEV_EVIDENCE_CLAIMS.csv").exists()
    assert (tmp_path / "NUTEV_CLAIM_EVALUATIONS.csv").exists()
    assert (tmp_path / "NUTEV_CONFLICTS.csv").exists()
    assert (tmp_path / "NUTEV_RECOMMENDATION_CANDIDATES.csv").exists()
    assert summary["evidence_claims_total"] >= 1
    assert summary["recommendation_candidates_total"] >= 1


def test_recommendation_candidates_are_never_final(tmp_path: Path):
    rows = [
        {
            "document_id": "doc_2",
            "title": "Guideline should reduce ultra-processed foods.",
            "abstract": "Guideline should reduce ultra-processed foods in obesity care.",
            "extracted_text": "Guideline should reduce ultra-processed foods in obesity care.",
            "source_provider": "demo",
            "source_type": "clinical_guideline",
        }
    ]

    write_audit_artifacts(rows, tmp_path)
    candidates = _rows(tmp_path / "NUTEV_RECOMMENDATION_CANDIDATES.csv")

    assert candidates
    assert all(row.get("recommendation_status") != "approved_for_protocol" for row in candidates)
    assert all(row.get("human_approval_status") == "not_reviewed" for row in candidates)


def test_audit_and_convergence_writes_csvs_and_matrices(tmp_path: Path):
    # Real-run parity (C3): audit CSVs land in the metadata dir (UI read location),
    # and the derived matrices land in the tables dir — previously produced only by
    # `nutev demo-data`, so a real run left the dashboard panels empty.
    meta = tmp_path / "02_metadata"
    tables = tmp_path / "06_tables"
    meta.mkdir()
    tables.mkdir()
    rows = [
        {
            "document_id": "doc_1",
            "title": "Guideline should reduce ultra-processed foods for obesity care.",
            "abstract": "The guideline should reduce ultra-processed foods in adults with obesity.",
            "extracted_text": "The guideline should reduce ultra-processed foods in adults with obesity.",
            "source_provider": "pubmed",
            "source_type": "clinical_guideline",
            "clinical_conditions": ["obesity"],
            "diet_patterns": ["plant_forward"],
            "outcomes": ["weight_management"],
        }
    ]

    summary = write_audit_and_convergence(rows, meta, tables)

    # Audit CSVs in the metadata dir (where the dashboard/API read).
    assert (meta / "NUTEV_EVIDENCE_CLAIMS.csv").exists()
    assert (meta / "NUTEV_RECOMMENDATION_CANDIDATES.csv").exists()
    # Derived matrices in the tables dir (where the dashboard reads).
    assert (tables / "NUTEV_EVIDENCE_CONVERGENCE_MATRIX.xlsx").exists()
    assert (tables / "NUTEV_EVIDENCE_GAP_REGISTER.xlsx").exists()
    assert (tables / "NUTEV_PROTOCOL_READINESS_MATRIX.xlsx").exists()
    assert summary["evidence_claims_total"] >= 1
    assert "convergence_stage_error" not in summary
    assert "evidence_convergence_total" in summary


def test_audit_and_convergence_is_empty_safe(tmp_path: Path):
    meta = tmp_path / "02_metadata"
    tables = tmp_path / "06_tables"
    meta.mkdir()
    tables.mkdir()

    summary = write_audit_and_convergence([], meta, tables)

    assert summary["evidence_claims_total"] == 0
    # Well-formed empty artifacts, no crash, no swallowed error.
    assert (meta / "NUTEV_EVIDENCE_CLAIMS.csv").exists()
    assert (tables / "NUTEV_EVIDENCE_CONVERGENCE_MATRIX.xlsx").exists()
    assert "convergence_stage_error" not in summary
