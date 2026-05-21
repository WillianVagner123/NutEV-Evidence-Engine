from nutev.audit.claim_evaluator import detect_conflicts, evaluate_claim
from nutev.audit.models import EvidenceClaim


def test_computational_inference_needs_review():
    c = EvidenceClaim(claim_id="c1", document_id="d1", claim_text="Prefer x", claim_status="inference_only", evidence_type="computational_inference")
    e = evaluate_claim(c, {})
    assert e.decision == "needs_human_review"


def test_conflicts_registered_not_deleted():
    a = EvidenceClaim(claim_id="a", document_id="d1", claim_text="Increase fiber intake", nutev_domains=["diet"])
    b = EvidenceClaim(claim_id="b", document_id="d2", claim_text="Reduce fiber intake", nutev_domains=["diet"])
    conflicts = detect_conflicts([a, b])
    assert conflicts and conflicts[0]["type"] == "possible_conflict"
