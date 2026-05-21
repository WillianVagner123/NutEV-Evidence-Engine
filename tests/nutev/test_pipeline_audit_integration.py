from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from nutev.analysis.nutev_classifier import classify_evidence
from nutev.audit.audit_export import export_audit_outputs
from nutev.audit.claim_evaluator import detect_conflicts, evaluate_claims
from nutev.audit.claim_extractor import extract_candidate_claims_from_record
from nutev.audit.models import AuditEvent
from nutev.audit.recommendation_registry import generate_recommendation_candidates
from nutev.export.excel_writer import write_excel_file
from nutev.settings import load_json


def test_pipeline_audit_integration(tmp_path: Path):
    fixture = Path("tests/fixtures/nutev_audit_records.json")
    records = json.loads(fixture.read_text(encoding="utf-8"))

    ontology = load_json(Path("config/nutev_ontology.json"))
    lenses = load_json(Path("config/evidence_lenses.json"))
    audit_rules = load_json(Path("config/audit_rules.json"))
    recommendation_rules = load_json(Path("config/recommendation_rules.json"))

    # 1) EvidenceRecords enriched by global classifier
    records = classify_evidence(records, ontology, lenses)
    assert all("domains" in r and "evidence_lenses" in r for r in records)

    # 2) EvidenceClaims
    claims = []
    for rec in records:
        claims.extend(extract_candidate_claims_from_record(rec, ontology, audit_rules))
    assert claims, "Expected claims from fixture records"

    # 3) ClaimEvaluations
    evaluations = evaluate_claims(claims, audit_rules)
    assert evaluations and len(evaluations) == len(claims)

    # 4) RecommendationCandidates
    recommendations = generate_recommendation_candidates(claims, evaluations, recommendation_rules)
    assert recommendations

    # Required validation: no ready recommendation without supporting_claim_ids
    blocked = {"evidence_linked", "ready_for_human_review", "approved_for_protocol"}
    for rec in recommendations:
        if rec.recommendation_status in blocked:
            assert rec.supporting_claim_ids

    # Required validation: claim locations preserved for literal text
    assert any(c.quote_location in {"title", "abstract", "extracted_text"} for c in claims)

    # Required validation: inference_only not final approval
    inference_ids = {c.claim_id for c in claims if c.claim_status == "inference_only"}
    for rec in recommendations:
        if set(rec.supporting_claim_ids) & inference_ids:
            assert rec.recommendation_status != "approved_for_protocol"

    # 5) HumanReviewQueue + audit exports
    conflicts = detect_conflicts(claims)
    events = [
        AuditEvent(
            audit_event_id="audit_e2e_1",
            run_id="run_e2e",
            event_stage="recommendation_generation",
            event_type="created",
            event_message="integration test event",
            meta_json={"claims": len(claims)},
        )
    ]
    tables_dir = tmp_path / "project_output" / "06_tables"
    metadata_dir = tmp_path / "project_output" / "02_metadata"
    export_audit_outputs(claims, evaluations, recommendations, events, conflicts, tables_dir, metadata_dir)

    # 6) GlobalEvidenceMatrix and 7) ProtocolTranslationMatrix
    df = pd.DataFrame([r for r in records])
    write_excel_file(df, tables_dir / "NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx")
    proto_cols = [c for c in df.columns if c.startswith("domain_") or c.startswith("outcome_")] + ["document_id", "title", "workstream"]
    write_excel_file(df[proto_cols], tables_dir / "NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx")

    # Validate files generated (xlsx or csv fallback)
    expected = [
        "NUTEV_EVIDENCE_CLAIMS",
        "NUTEV_RECOMMENDATION_CANDIDATES",
        "NUTEV_HUMAN_REVIEW_QUEUE",
        "NUTEV_GLOBAL_EVIDENCE_MATRIX",
        "NUTEV_PROTOCOL_TRANSLATION_MATRIX",
    ]
    for stem in expected:
        assert (tables_dir / f"{stem}.xlsx").exists() or (tables_dir / f"{stem}.csv").exists()

    # Summary fields equivalent to run_summary additions
    summary = {
        "evidence_claims_total": len(claims),
        "evidence_claims_supported": sum(1 for c in claims if c.claim_status == "supported"),
        "evidence_claims_needs_review": sum(1 for c in claims if c.needs_human_review),
        "recommendation_candidates_total": len(recommendations),
        "recommendation_candidates_ready_review": sum(1 for r in recommendations if r.recommendation_status == "ready_for_human_review"),
        "recommendation_candidates_insufficient_evidence": sum(1 for r in recommendations if r.recommendation_status == "insufficient_evidence"),
        "conflicting_evidence_total": len(conflicts),
    }
    assert summary["evidence_claims_total"] > 0
