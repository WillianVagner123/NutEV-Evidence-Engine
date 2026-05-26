from __future__ import annotations

import csv
from pathlib import Path

from nutev.export.audit_artifacts import write_audit_artifacts


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
