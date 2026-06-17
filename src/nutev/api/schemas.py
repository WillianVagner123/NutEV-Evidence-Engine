from __future__ import annotations

from pydantic import BaseModel


class ApiStatus(BaseModel):
    status: str
    project_root: str
    service: str = "nutev-platform"


class MissingArtifactResponse(BaseModel):
    available: bool = False
    message: str


class PaginatedResponse(BaseModel):
    available: bool = True
    total: int
    limit: int
    offset: int
    items: list[dict]


class HumanReviewDecisionIn(BaseModel):
    item_type: str
    item_id: str
    reviewer_name: str
    reviewer_role: str
    reviewer_decision: str
    reviewer_notes: str = ""
    final_decision: str


class HumanReviewDecisionOut(HumanReviewDecisionIn):
    decision_id: str
    decision_date: str
    created_at: str


class ArtifactInfo(BaseModel):
    file_name: str
    relative_path: str
    size_bytes: int
    modified_at: str
    artifact_type: str


class RunRequest(BaseModel):
    workstreams: list[str] | None = None
    web_enabled: bool = False
    journal_quality: bool = False
