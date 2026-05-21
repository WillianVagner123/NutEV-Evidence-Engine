from nutev.audit.models import EvidenceClaim, RecommendationCandidate


def test_evidence_claim_requires_document_id():
    try:
        EvidenceClaim(claim_id="c1", document_id="", claim_text="x")
        assert False
    except Exception:
        assert True


def test_claim_without_quote_moves_to_needs_human_review():
    c = EvidenceClaim(claim_id="c1", document_id="d1", claim_text="x", claim_status="supported", exact_quote=None)
    assert c.claim_status == "needs_human_review"


def test_recommendation_without_support_not_ready():
    r = RecommendationCandidate(recommendation_id="r1", recommendation_text="t", protocol_component="p", recommendation_status="ready_for_human_review", supporting_claim_ids=[])
    assert r.recommendation_status == "draft_needs_evidence"
