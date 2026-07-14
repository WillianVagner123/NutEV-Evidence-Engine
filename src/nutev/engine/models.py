from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from nutev.engine.enums import DownloadStatus, EventKind
from nutev.engine.validators import (
    assert_status_coherence,
    normalize_doi,
    normalize_pmcid,
    normalize_pmid,
    normalize_url,
    validate_capture_status,
    validate_download_status,
    validate_extraction_status,
    validate_failure_reason,
    validate_workstream,
)


class SearchCase(BaseModel):
    case_id: str
    name: str
    workstreams: list[str]
    mode: str
    since_days: int | None = None
    country_discovery: bool = False
    official_crawl: bool = True
    web_enabled: bool = True
    browser_enabled: bool = False
    llm_enabled: bool = False
    providers_enabled: list[str] = Field(default_factory=list)
    created_at: datetime
    config_version: str = "v1"

    @field_validator("workstreams")
    @classmethod
    def _validate_workstreams(cls, value: list[str]) -> list[str]:
        return [validate_workstream(item) or item for item in value]


class SearchJob(BaseModel):
    job_id: str
    case_id: str
    run_id: str
    started_at: datetime
    finished_at: datetime | None = None
    git_commit: str | None = None
    cli_args: list[str] = Field(default_factory=list)
    config_snapshot_path: str | None = None
    status: str = "running"


class DocumentCandidate(BaseModel):
    document_id: str
    title: str | None = None
    original_url: str | None = None
    final_url: str | None = None
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    year: int | None = None
    language: str | None = None
    source_provider: str | None = None
    source_institution: str | None = None
    country: str | None = None
    region: str | None = None
    workstream: str | None = None
    raw_score: float | None = None
    relevance_score: float | None = None
    novelty_score: float | None = None
    evidence_type: str | None = None
    created_at: datetime

    @field_validator("doi", mode="before")
    @classmethod
    def _normalize_doi(cls, value):
        return normalize_doi(value)

    @field_validator("pmid", mode="before")
    @classmethod
    def _normalize_pmid(cls, value):
        return normalize_pmid(value)

    @field_validator("pmcid", mode="before")
    @classmethod
    def _normalize_pmcid(cls, value):
        return normalize_pmcid(value)

    @field_validator("original_url", "final_url", mode="before")
    @classmethod
    def _normalize_url(cls, value):
        return normalize_url(value)

    @field_validator("workstream", mode="before")
    @classmethod
    def _validate_workstream(cls, value):
        return validate_workstream(value)


class ProviderHit(BaseModel):
    provider: str
    query: str
    title: str
    url: str
    doi: str | None = None
    year: int | None = None
    abstract: str | None = None
    journal: str | None = None
    authors: list[str] = Field(default_factory=list)
    raw_json: dict[str, Any] = Field(default_factory=dict)
    workstream: str | None = None

    @field_validator("url", mode="before")
    @classmethod
    def _normalize_url(cls, value):
        normalized = normalize_url(value)
        if not normalized:
            raise ValueError("ProviderHit.url must be a valid http(s) URL")
        return normalized

    @field_validator("doi", mode="before")
    @classmethod
    def _normalize_doi(cls, value):
        return normalize_doi(value)

    @field_validator("workstream", mode="before")
    @classmethod
    def _validate_workstream(cls, value):
        return validate_workstream(value)


class DownloadResult(BaseModel):
    document_id: str
    status: DownloadStatus
    original_url: str | None = None
    final_url: str | None = None
    artifact_path: str | None = None
    content_type: str | None = None
    http_status: int | None = None
    failure_reason: str | None = None
    host: str | None = None
    created_at: datetime

    @field_validator("original_url", "final_url", mode="before")
    @classmethod
    def _normalize_url(cls, value):
        return normalize_url(value)

    @field_validator("failure_reason", mode="before")
    @classmethod
    def _validate_failure_reason(cls, value):
        return validate_failure_reason(value)


class CaptureResult(BaseModel):
    document_id: str
    status: str
    html_path: str | None = None
    txt_path: str | None = None
    json_path: str | None = None
    screenshot_path: str | None = None
    title: str | None = None
    abstract: str | None = None
    headings: list[str] = Field(default_factory=list)
    pdf_links_found: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("status", mode="before")
    @classmethod
    def _validate_status(cls, value):
        return validate_capture_status(value)


class ExtractionResult(BaseModel):
    document_id: str
    artifact_path: str | None = None
    text_path: str | None = None
    extraction_status: str
    chars: int | None = None
    used_ocr: bool = False
    ocr_failed_pages: list[int] = Field(default_factory=list)
    failure_reason: str | None = None

    @field_validator("extraction_status", mode="before")
    @classmethod
    def _validate_status(cls, value):
        return validate_extraction_status(value)

    @field_validator("failure_reason", mode="before")
    @classmethod
    def _validate_failure_reason(cls, value):
        return validate_failure_reason(value)


class EvidenceRecord(BaseModel):
    document_id: str
    title: str | None = None
    doi: str | None = None
    url: str | None = None
    workstream: str | None = None
    source_provider: str | None = None
    source_institution: str | None = None
    country: str | None = None
    region: str | None = None
    year: int | None = None
    evidence_type: str | None = None
    capture_status: str | None = None
    download_status: str | None = None
    extraction_status: str | None = None
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    relevance_score: float | None = None
    novelty_score: float | None = None
    llm_decision: str | None = None
    llm_reason: str | None = None
    domains: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    diet_patterns: list[str] = Field(default_factory=list)
    evidence_lenses: list[str] = Field(default_factory=list)
    ontology_version: str | None = None
    classifier_version: str = "nutev_classifier_v1"
    clinical_conditions: list[str] = Field(default_factory=list)

    # --- Article 1 analytical schema (see nutev.analysis.article1_coding) --------
    # PRISMA track and provenance (Task P2). track is one of
    # guideline_repository | indexed_database | society_website |
    # reference_chaining | hand_search | linked_implementation_material.
    track: str | None = None
    issuing_body: str | None = None
    who_region: str | None = None
    income_band: str | None = None
    document_version: str | None = None
    access_date: str | None = None
    official_url: str | None = None
    archived_pdf_path: str | None = None
    archived_pdf_sha256: str | None = None
    # A/B/C/D analytical domains (Task P1). Assistive coding; human confirms.
    domain_A: bool = False
    domain_B: bool = False
    domain_C: bool = False
    domain_D: bool = False
    profile: str | None = None
    n_domains: int = 0
    mentions_cost: bool = False
    mentions_equity: bool = False
    domain_coding_needs_human_review: bool = True
    # AACODS grey-literature appraisal (Task P3).
    authority: str | None = None
    accuracy: str | None = None
    coverage: str | None = None
    objectivity: str | None = None
    date_currency: str | None = None
    significance: str | None = None
    aacods_needs_human_review: bool = True

    @field_validator("doi", mode="before")
    @classmethod
    def _normalize_doi(cls, value):
        return normalize_doi(value)

    @field_validator("url", mode="before")
    @classmethod
    def _normalize_url(cls, value):
        return normalize_url(value)

    @field_validator("workstream", mode="before")
    @classmethod
    def _validate_workstream(cls, value):
        return validate_workstream(value)

    @field_validator("capture_status", mode="before")
    @classmethod
    def _validate_capture_status(cls, value):
        return validate_capture_status(value)

    @field_validator("download_status", mode="before")
    @classmethod
    def _validate_download_status(cls, value):
        return validate_download_status(value)

    @field_validator("extraction_status", mode="before")
    @classmethod
    def _validate_extraction_status(cls, value):
        return validate_extraction_status(value)

    @model_validator(mode="after")
    def _validate_status_coherence(self):
        assert_status_coherence(
            {
                "download_status": self.download_status,
                "capture_status": self.capture_status,
                "extraction_status": self.extraction_status,
                "artifact_paths": self.artifact_paths,
            }
        )
        return self


class RunEvent(BaseModel):
    run_id: str
    event_at: datetime
    event_kind: EventKind
    stage: str
    provider: str | None = None
    host: str | None = None
    document_id: str | None = None
    message: str
    meta_json: dict[str, Any] = Field(default_factory=dict)
