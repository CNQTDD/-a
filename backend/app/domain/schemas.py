from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import (
    FeedbackAction,
    RiskLevel,
    SessionStatus,
    SourceType,
    ValidationStatus,
)

# ── Session ──────────────────────────────────────────────────────────────────


class SessionCreate(BaseModel):
    user_id: str
    complaint_text: str = Field(min_length=1, max_length=10000)
    client_request_id: str | None = None


class IntentResult(BaseModel):
    intent: str
    emotion: str
    request: str
    entities: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    risk_signals: list[str] = Field(default_factory=list)


class RetrievedEvidenceItem(BaseModel):
    evidence_id: str
    source_id: str
    chunk_id: str
    source_type: SourceType
    title: str
    content_snapshot: str
    score: float
    rerank_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedSolution(BaseModel):
    solution_text: str
    cited_evidence_ids: list[str] = Field(default_factory=list)
    assessment: str = ""
    steps: list[str] = Field(default_factory=list)
    risk_notice: str = ""


class ValidationResult(BaseModel):
    status: ValidationStatus
    reason_codes: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    recommended_route: str = "human_review"


class WorkflowEvent(BaseModel):
    event_id: str
    session_id: str
    run_id: str
    trace_id: str
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    status: SessionStatus
    risk_level: RiskLevel | None = None
    intent: dict[str, Any] | None = None
    entities: dict[str, Any] | None = None
    confidence: float | None = None
    evidence: list[RetrievedEvidenceItem] = Field(default_factory=list)
    solution: GeneratedSolution | None = None
    validation: ValidationResult | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SessionListItem(BaseModel):
    id: str
    user_id: str
    status: SessionStatus
    risk_level: RiskLevel | None = None
    intent_summary: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SessionListResponse(BaseModel):
    items: list[SessionListItem]
    cursor: str | None = None


# ── Feedback ─────────────────────────────────────────────────────────────────


class FeedbackCreate(BaseModel):
    action: FeedbackAction
    edited_solution: str | None = None
    reject_reason: str | None = None
    operator_note: str | None = None

    @model_validator(mode="after")
    def _validate_required_fields(self) -> "FeedbackCreate":
        if self.action == FeedbackAction.REJECTED and not self.reject_reason:
            raise ValueError("rejected feedback requires a reason")
        if self.action == FeedbackAction.EDITED and not self.edited_solution:
            raise ValueError("edited feedback requires a solution")
        return self


class FeedbackResponse(BaseModel):
    id: str
    session_id: str
    action: FeedbackAction
    edited_solution: str | None = None
    reject_reason: str | None = None
    operator_note: str | None = None
    created_at: datetime | None = None


# ── Knowledge ────────────────────────────────────────────────────────────────


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    source_types: list[SourceType] | None = None
    business_type: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResult(BaseModel):
    items: list[RetrievedEvidenceItem]
    degraded_sources: list[str] = Field(default_factory=list)
    total: int = 0


# ── Metrics ──────────────────────────────────────────────────────────────────


class MetricsSummary(BaseModel):
    total_sessions: int = 0
    completed_sessions: int = 0
    adoption_rate: float = 0.0
    avg_handling_time_seconds: float = 0.0
    api_success_rate: float = 0.0
