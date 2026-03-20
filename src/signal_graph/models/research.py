from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from signal_graph.models.policy import ScoringPolicy


class ResearchBundleInput(BaseModel):
    supporting_documents: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    entity_resolution_results: dict[str, str] | None = None
    evidence_spans: list[str] = Field(default_factory=list)
    research_confidence: float = 0.0
    research_notes: str | None = None

    def is_empty(self) -> bool:
        return not any(
            [
                self.supporting_documents,
                self.contradictions,
                self.entity_resolution_results,
                self.evidence_spans,
                (self.research_notes or "").strip(),
            ]
        )


class ResearchBundle(BaseModel):
    research_bundle_id: str
    event_candidate_id: str
    bundle_revision: int = 1
    scoring_policy_snapshot: ScoringPolicy | None = None
    supporting_documents: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    entity_resolution_results: dict[str, str] | None = None
    evidence_spans: list[str] = Field(default_factory=list)
    research_confidence: float = 0.0
    research_notes: str | None = None
    created_at: datetime | None = None
