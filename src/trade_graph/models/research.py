from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchBundle(BaseModel):
    research_bundle_id: str
    event_candidate_id: str
    supporting_documents: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    entity_resolution_results: dict[str, str] | None = None
    evidence_spans: list[str] = Field(default_factory=list)
    research_confidence: float = 0.0
    research_notes: str | None = None

