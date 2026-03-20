from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EventCandidate(BaseModel):
    event_candidate_id: str
    title: str
    event_type: str
    direction: str
    primary_entities: list[str]
    dedupe_fingerprint: str | None = None
    secondary_entities: list[str] = Field(default_factory=list)
    source_item_ids: list[str] = Field(default_factory=list)
    candidate_confidence: float = 0.0
    candidate_status: str = "pending"
    created_at: datetime | None = None
