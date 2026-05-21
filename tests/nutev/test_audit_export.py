from pathlib import Path
from nutev.audit.audit_export import export_audit_outputs
from nutev.audit.models import AuditEvent, ClaimEvaluation, EvidenceClaim, RecommendationCandidate


def test_export_generates_xlsx(tmp_path: Path):
    claims = [EvidenceClaim(claim_id="c1", document_id="d1", claim_text="Adults should reduce ultra-processed foods", nutev_domains=["food_processing"], exact_quote="Adults should reduce ultra-processed foods", claim_status="supported", needs_human_review=False, evidence_type="extracted_quote")]
    evals = [ClaimEvaluation(evaluation_id="e1", claim_id="c1", document_id="d1", evaluator_type="rule_based", reason="ok", decision="accept_for_synthesis")]
    recs = [RecommendationCandidate(recommendation_id="r1", recommendation_text="Reduce ultra-processed foods", protocol_component="diretrizes_dieteticas", supporting_claim_ids=["c1"], supporting_document_ids=["d1"], recommendation_status="ready_for_human_review")]
    events = [AuditEvent(audit_event_id="a1", run_id="run", document_id="d1", claim_id="c1", recommendation_id="r1", event_stage="recommendation_generation", event_type="created", event_message="created")]
    export_audit_outputs(claims, evals, recs, events, [], tmp_path / "06_tables", tmp_path / "02_metadata")
    assert (tmp_path / "06_tables" / "NUTEV_EVIDENCE_CLAIMS.xlsx").exists() or (tmp_path / "06_tables" / "NUTEV_EVIDENCE_CLAIMS.csv").exists()
    assert (tmp_path / "06_tables" / "NUTEV_RECOMMENDATION_CANDIDATES.xlsx").exists() or (tmp_path / "06_tables" / "NUTEV_RECOMMENDATION_CANDIDATES.csv").exists()
    assert (tmp_path / "06_tables" / "NUTEV_HUMAN_REVIEW_QUEUE.xlsx").exists() or (tmp_path / "06_tables" / "NUTEV_HUMAN_REVIEW_QUEUE.csv").exists()
