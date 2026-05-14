from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from nutev.engine.enums import DownloadStatus, EventKind


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


class ExtractionResult(BaseModel):
    document_id: str
    artifact_path: str | None = None
    text_path: str | None = None
    extraction_status: str
    chars: int | None = None
    used_ocr: bool = False
    ocr_failed_pages: list[int] = Field(default_factory=list)
    failure_reason: str | None = None


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
    clinical_conditions: list[str] = Field(default_factory=list)


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
