from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

ClaimStatus = Literal[
    "supported",
    "partially_supported",
    "conflicting",
    "insufficient_evidence",
    "needs_human_review",
    "excluded",
    "inference_only",
]
HumanValidationStatus = Literal[
    "not_reviewed", "approved", "revised", "rejected", "needs_second_reviewer"
]
EvidenceType = Literal[
    "official_guideline", "clinical_guideline", "consensus_statement", "position_statement",
    "scientific_statement", "systematic_review", "umbrella_review", "randomized_trial",
    "implementation_study", "grey_literature", "extracted_quote", "computational_inference", "human_annotation"
]
Decision = Literal[
    "accept_for_synthesis", "accept_with_caution", "reject", "needs_human_review", "insufficient_evidence", "conflicting_evidence"
]
RecommendationStatus = Literal[
    "draft_needs_evidence", "evidence_linked", "insufficient_evidence", "conflicting_evidence",
    "ready_for_human_review", "approved_for_protocol", "rejected"
]
EventStage = Literal[
    "document_discovery", "document_capture", "text_extraction", "domain_classification", "claim_extraction",
    "claim_evaluation", "recommendation_generation", "human_review", "protocol_translation"
]
EventType = Literal["created", "updated", "warning", "rejected", "approved", "insufficient_evidence", "conflicting_evidence", "needs_human_review"]


class EvidenceClaim(BaseModel):
    claim_id: str
    document_id: str
    run_id: str | None = None
    title: str | None = None
    source_url: str | None = None
    source_type: str | None = None
    source_provider: str | None = None
    source_institution: str | None = None
    country: str | None = None
    year: int | None = None
    claim_text: str
    exact_quote: str | None = None
    quote_location: str | None = None
    quote_char_start: int | None = None
    quote_char_end: int | None = None
    evidence_type: EvidenceType = "computational_inference"
    nutev_domains: list[str] = Field(default_factory=list)
    clinical_conditions: list[str] = Field(default_factory=list)
    dietary_patterns: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    protocol_components: list[str] = Field(default_factory=list)
    evidence_lenses: list[str] = Field(default_factory=list)
    computational_confidence: float | None = None
    extraction_method: str = "deterministic_rules"
    extraction_status: str = "ok"
    claim_status: ClaimStatus = "needs_human_review"
    needs_human_review: bool = True
    human_validation_status: HumanValidationStatus = "not_reviewed"
    human_reviewer: str | None = None
    human_notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _require_claim_content(self):
        if not (self.document_id or "").strip():
            raise ValueError("EvidenceClaim.document_id is required")
        if not (self.claim_text or "").strip():
            raise ValueError("EvidenceClaim.claim_text is required")
        if self.claim_status in {"supported", "partially_supported"} and not self.exact_quote:
            self.claim_status = "needs_human_review"
            self.needs_human_review = True
        return self


class ClaimEvaluation(BaseModel):
    evaluation_id: str
    claim_id: str
    document_id: str
    evaluator_type: str
    evaluator_name: str | None = None
    positive_support: float | None = None
    negative_support: float | None = None
    uncertainty: float | None = None
    evidence_quality_note: str | None = None
    reason: str
    decision: Decision
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecommendationCandidate(BaseModel):
    recommendation_id: str
    recommendation_text: str
    protocol_component: str
    nutev_domains: list[str] = Field(default_factory=list)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    supporting_document_ids: list[str] = Field(default_factory=list)
    conflicting_claim_ids: list[str] = Field(default_factory=list)
    evidence_lenses: list[str] = Field(default_factory=list)
    clinical_conditions: list[str] = Field(default_factory=list)
    dietary_patterns: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    population_applicability: str | None = None
    implementation_considerations: str | None = None
    strength_placeholder: str | None = None
    evidence_gap: str | None = None
    recommendation_status: RecommendationStatus = "draft_needs_evidence"
    human_approval_status: HumanValidationStatus = "not_reviewed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _validate_support(self):
        blocked = {"evidence_linked", "ready_for_human_review", "approved_for_protocol"}
        if self.recommendation_status in blocked and not self.supporting_claim_ids:
            self.recommendation_status = "draft_needs_evidence"
        if self.recommendation_status == "approved_for_protocol":
            self.recommendation_status = "ready_for_human_review"
        return self


class AuditEvent(BaseModel):
    audit_event_id: str
    run_id: str
    document_id: str | None = None
    claim_id: str | None = None
    recommendation_id: str | None = None
    event_stage: EventStage
    event_type: EventType
    event_message: str
    meta_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
