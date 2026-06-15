from __future__ import annotations

import hashlib
import re
from nutev.audit.models import ClaimEvaluation, EvidenceClaim


GUIDELINE_HINTS = {"guideline", "official", "clinical_society", "clinical"}


def _has_word(text: str, word: str) -> bool:
    """Whole-word match so 'high'/'low' don't fire on 'highlights'/'below'."""
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def _eval_id(claim_id: str) -> str:
    return f"eval_{hashlib.sha1(claim_id.encode()).hexdigest()[:16]}"  # noqa: S324


def evaluate_claim(claim: EvidenceClaim, audit_rules: dict) -> ClaimEvaluation:
    decision = "accept_with_caution"
    reason = "Claim accepted with caution."
    pos, neg, unc = 0.5, 0.0, 0.5

    if not claim.document_id or not claim.claim_text:
        decision, reason, pos, neg, unc = "reject", "Missing required claim fields.", 0.0, 1.0, 1.0
    elif claim.claim_status == "conflicting":
        decision, reason, neg, unc = "needs_human_review", "Conflicting claim status.", 0.6, 0.8
    elif claim.claim_status == "insufficient_evidence":
        decision, reason, neg, unc = "insufficient_evidence", "Claim marked as insufficient evidence.", 0.8, 0.9
    elif not claim.exact_quote and claim.claim_status != "inference_only":
        decision, reason, unc = "needs_human_review", "Missing exact quote for non-inference claim.", 0.9
    elif claim.evidence_type == "computational_inference":
        decision, reason, unc = "needs_human_review", "Computational inference requires human validation.", 0.9

    if any(h in (claim.source_type or "").lower() for h in GUIDELINE_HINTS):
        pos = min(1.0, pos + 0.2)

    return ClaimEvaluation(
        evaluation_id=_eval_id(claim.claim_id),
        claim_id=claim.claim_id,
        document_id=claim.document_id,
        evaluator_type="rule_based",
        reason=reason,
        decision=decision,
        positive_support=pos,
        negative_support=neg,
        uncertainty=unc,
    )


def evaluate_claims(claims: list[EvidenceClaim], audit_rules: dict) -> list[ClaimEvaluation]:
    return [evaluate_claim(c, audit_rules) for c in claims]


def detect_conflicts(claims: list[EvidenceClaim]) -> list[dict]:
    opposites = [("increase", "reduce"), ("encourage", "avoid"), ("high", "low"), ("liberal", "restrict")]
    results = []
    for i, c1 in enumerate(claims):
        t1 = c1.claim_text.lower()
        for c2 in claims[i + 1 :]:
            if set(c1.nutev_domains).isdisjoint(set(c2.nutev_domains)):
                continue
            t2 = c2.claim_text.lower()
            if any(
                (_has_word(t1, a) and _has_word(t2, b)) or (_has_word(t1, b) and _has_word(t2, a))
                for a, b in opposites
            ):
                results.append({"type": "possible_conflict", "claim_id_a": c1.claim_id, "claim_id_b": c2.claim_id, "domains": sorted(set(c1.nutev_domains) & set(c2.nutev_domains))})
    return results
