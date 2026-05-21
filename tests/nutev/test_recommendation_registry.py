from nutev.audit.models import ClaimEvaluation, EvidenceClaim
from nutev.audit.recommendation_registry import generate_recommendation_candidates


def test_no_approved_from_inference_alone():
    c = EvidenceClaim(claim_id="c1", document_id="d1", claim_text="x", claim_status="inference_only", evidence_type="computational_inference", protocol_components=["diretrizes_dieteticas"], nutev_domains=["diet"])
    e = ClaimEvaluation(evaluation_id="e1", claim_id="c1", document_id="d1", evaluator_type="rule_based", reason="r", decision="needs_human_review")
    recs = generate_recommendation_candidates([c], [e], {})
    assert recs
    assert recs[0].recommendation_status != "approved_for_protocol"
