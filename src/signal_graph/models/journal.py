from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

IntentStatus = Literal["explicit", "inferred", "unknown"]
OriginType = Literal["user", "agent_artifact", "external_reference"]
RecallView = Literal["ranked", "timeline", "session"]
MINIMUM_PROVENANCE_FIELDS = [
    "signal_id",
    "origin_type",
    "actor_session_identity",
    "graph_or_file_reference",
    "intent_status",
]
NON_SEMANTIC_DETERMINISM_FIELDS = ["artifact_id", "created_at", "artifact_path"]
RECALL_ORDERING_PRECEDENCE = {
    "ranked": ["score", "observed_at|captured_at|published_at", "signal_id"],
    "timeline": ["observed_at|captured_at|published_at", "score", "signal_id"],
    "session": [
        "group_latest_observed_at|captured_at|published_at",
        "group_key",
        "score",
        "signal_id",
    ],
}


class JournalSignal(BaseModel):
    signal_id: str
    origin_type: OriginType
    source_name: str
    source_url: str | None = None
    source_ref: str | None = None
    raw_text: str
    raw_payload: str | None = None
    content_hash: str
    captured_at: datetime | None = None
    observed_at: datetime | None = None
    published_at: datetime | None = None
    agent_host: str | None = None
    agent_process: str | None = None
    agent_runtime: str | None = None
    agent_session_id: str | None = None
    agent_role: str | None = None
    workspace_path: str | None = None
    intent_status: IntentStatus = "unknown"
    why_text: str | None = None
    who_refs: list[str] = Field(default_factory=list)
    what_refs: list[str] = Field(default_factory=list)
    where_refs: list[str] = Field(default_factory=list)
    how_refs: list[str] = Field(default_factory=list)
    graph_path: list[str] = Field(default_factory=list)
    journaled_at: datetime | None = None


class RecallQuery(BaseModel):
    raw_query: str = ""
    tokens: list[str] = Field(default_factory=list)
    exact_phrases: list[str] = Field(default_factory=list)
    origin_type: OriginType | None = None
    session_id: str | None = None
    runtime_family: str | None = None
    source_name: str | None = None
    view: RecallView = "ranked"
    limit: int = 5


class RecallMatchExplanation(BaseModel):
    matched_fields: list[str] = Field(default_factory=list)
    phrase_hits: list[str] = Field(default_factory=list)
    filter_matches: dict[str, str] = Field(default_factory=dict)
    score_components: dict[str, float] = Field(default_factory=dict)
    graph_path_labels: list[str] = Field(default_factory=list)
    intent_status_note: str = ""


class RecallMatch(BaseModel):
    signal: JournalSignal
    score: float
    explanation: RecallMatchExplanation


class RecallSessionGroup(BaseModel):
    session_key: str
    latest_timestamp: datetime | None = None
    signal_ids: list[str] = Field(default_factory=list)
    matches: list[RecallMatch] = Field(default_factory=list)


class RecallResult(BaseModel):
    view: RecallView = "ranked"
    query_contract: RecallQuery
    ordering_precedence: list[str] = Field(default_factory=list)
    matches: list[RecallMatch] = Field(default_factory=list)
    session_groups: list[RecallSessionGroup] = Field(default_factory=list)


class RecallArtifact(BaseModel):
    artifact_id: str
    query: str
    signal_ids: list[str] = Field(default_factory=list)
    view: RecallView = "ranked"
    query_contract: RecallQuery | None = None
    matches: list[RecallMatch] = Field(default_factory=list)
    session_groups: list[RecallSessionGroup] = Field(default_factory=list)
    markdown_text: str
    artifact_path: str | None = None
    graph_paths: dict[str, list[str]] = Field(default_factory=dict)
    provenance_contract: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
