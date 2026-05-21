from __future__ import annotations

import hashlib
from collections import defaultdict

from nutev.audit.models import ClaimEvaluation, EvidenceClaim, RecommendationCandidate


def build_recommendation_id(protocol_component: str, nutev_domains: list[str], recommendation_text: str) -> str:
    seed = f"{protocol_component}|{'|'.join(sorted(nutev_domains))}|{recommendation_text.lower()}"
    return f"rec_{hashlib.sha1(seed.encode()).hexdigest()[:16]}"  # noqa: S324


def validate_recommendation_candidate(candidate: RecommendationCandidate, recommendation_rules: dict) -> RecommendationCandidate:
    if not candidate.supporting_claim_ids and candidate.recommendation_status in {"evidence_linked", "ready_for_human_review", "approved_for_protocol"}:
        candidate.recommendation_status = "draft_needs_evidence"
    if candidate.recommendation_status == "approved_for_protocol":
        candidate.recommendation_status = "ready_for_human_review"
    return candidate


def detect_recommendation_conflicts(candidate: RecommendationCandidate, claims: list[EvidenceClaim]) -> RecommendationCandidate:
    conflicting = [c.claim_id for c in claims if c.claim_status == "conflicting" and c.claim_id in candidate.supporting_claim_ids]
    if conflicting:
        candidate.conflicting_claim_ids = sorted(set(candidate.conflicting_claim_ids + conflicting))
        candidate.recommendation_status = "conflicting_evidence"
    return candidate


def generate_recommendation_candidates(claims: list[EvidenceClaim], evaluations: list[ClaimEvaluation], recommendation_rules: dict) -> list[RecommendationCandidate]:
    accepted = {e.claim_id for e in evaluations if e.decision in {"accept_for_synthesis", "accept_with_caution", "needs_human_review"}}
    grouped: dict[tuple[str, str], list[EvidenceClaim]] = defaultdict(list)
    for c in claims:
        for comp in c.protocol_components or ["diretrizes_dieteticas"]:
            for d in c.nutev_domains or ["unspecified_domain"]:
                grouped[(comp, d)].append(c)

    out: list[RecommendationCandidate] = []
    for (comp, dom), grp in grouped.items():
        support = [c for c in grp if c.claim_id in accepted]
        status = "ready_for_human_review" if support else "draft_needs_evidence"
        rec = RecommendationCandidate(
            recommendation_id=build_recommendation_id(comp, [dom], f"Candidate recommendation for {comp} / {dom}"),
            recommendation_text=f"Candidate recommendation for {comp} in domain {dom}.",
            protocol_component=comp,
            nutev_domains=[dom],
            supporting_claim_ids=[c.claim_id for c in support],
            supporting_document_ids=sorted({c.document_id for c in support}),
            evidence_lenses=sorted({l for c in support for l in c.evidence_lenses}),
            clinical_conditions=sorted({x for c in support for x in c.clinical_conditions}),
            dietary_patterns=sorted({x for c in support for x in c.dietary_patterns}),
            outcomes=sorted({x for c in support for x in c.outcomes}),
            strength_placeholder="not_assessed",
            evidence_gap=None if support else "No supporting claims linked.",
            recommendation_status=status,
        )
        rec = detect_recommendation_conflicts(rec, grp)
        rec = validate_recommendation_candidate(rec, recommendation_rules)
        out.append(rec)
    return out
