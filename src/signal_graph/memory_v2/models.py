from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

HookPhase = Literal["pre_action", "post_output", "share_artifact"]


class CapturePolicy(BaseModel):
    auto_capture_observable_facts: bool = True
    require_confirmation_for_inferred_why: bool = True
    require_confirmation_for_sensitive_retention: bool = True


class WhyInference(BaseModel):
    text: str
    confidence: float


class PendingWhy(BaseModel):
    text: str
    confidence: float
    reason: str


class Owner(BaseModel):
    owner_id: str
    email: str
    display_name: str
    created_at: datetime


class Actor(BaseModel):
    actor_id: str
    owner_id: str
    runtime_family: str
    host: str
    session_id: str
    created_at: datetime


class MemoryEvent(BaseModel):
    event_id: str
    owner_id: str
    actor_id: str
    runtime_family: str
    host: str
    session_id: str
    phase: HookPhase
    action_text: str
    observed_facts: list[str] = Field(default_factory=list)
    topic_refs: list[str] = Field(default_factory=list)
    parent_event_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    why_inference: WhyInference | None = None
    pending_why: PendingWhy | None = None
    occurred_at: datetime
    created_at: datetime


class ArtifactShare(BaseModel):
    artifact_id: str
    owner_id: str
    actor_id: str
    title: str
    source_path: str
    canonical_raw_path: str
    sha256: str
    topic_refs: list[str] = Field(default_factory=list)
    share_event_id: str
    shared_at: datetime


class DerivedInterpretation(BaseModel):
    interpretation_id: str
    owner_id: str
    artifact_id: str
    source_event_id: str
    summary: str
    topics: list[str] = Field(default_factory=list)
    confidence: float
    markdown_view_path: str
    created_at: datetime


class Correction(BaseModel):
    correction_id: str
    owner_id: str
    target_id: str
    topic: str | None = None
    instruction: str
    created_at: datetime


class Redaction(BaseModel):
    redaction_id: str
    owner_id: str
    target_id: str
    reason: str
    created_at: datetime


class QueryResult(BaseModel):
    owner: Owner
    topic: str | None = None
    on_date: date | None = None
    events: list[MemoryEvent] = Field(default_factory=list)
    artifacts: list[ArtifactShare] = Field(default_factory=list)
    derived_interpretations: list[DerivedInterpretation] = Field(default_factory=list)
    guidance: list[str] = Field(default_factory=list)
    applied_corrections: list[Correction] = Field(default_factory=list)
    applied_redactions: list[Redaction] = Field(default_factory=list)


class ExplanationActor(BaseModel):
    actor_id: str
    runtime_family: str
    host: str
    session_id: str


class ExplanationResponse(BaseModel):
    owner: Owner
    actor: ExplanationActor
    action_text: str
    provenance_chain: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    why_inference: WhyInference | None = None
    active_corrections: list[Correction] = Field(default_factory=list)
    active_redactions: list[Redaction] = Field(default_factory=list)
    guidance: list[str] = Field(default_factory=list)
    is_redacted: bool = False
