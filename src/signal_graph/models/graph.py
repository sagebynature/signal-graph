from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GraphEvent(BaseModel):
    graph_event_id: str
    event_candidate_id: str
    committed_at: datetime | None = None
    trust_score: float = 0.0
    eligible_modes: list[str] = Field(default_factory=list)
    ingest_decision: str = "pending"


class RankedCandidate(BaseModel):
    ticker: str
    fast_reaction_score: float
    follow_through_score: float
    timing_window: str = "short_drift"
    matched_entity: str | None = None
    relationship_path: list[str] = Field(default_factory=list)
    reason_summary: str | None = None


class MemoResponse(BaseModel):
    graph_event_id: str
    ticker: str
    memo_text: str
    artifact_path: str | None = None
    ranked_candidates: list[RankedCandidate] = Field(default_factory=list)
