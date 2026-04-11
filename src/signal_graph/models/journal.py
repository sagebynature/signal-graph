from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

IntentStatus = Literal["explicit", "inferred", "unknown"]
OriginType = Literal["user", "agent_artifact", "external_reference"]
MINIMUM_PROVENANCE_FIELDS = [
    "signal_id",
    "origin_type",
    "actor_session_identity",
    "graph_or_file_reference",
    "intent_status",
]
NON_SEMANTIC_DETERMINISM_FIELDS = ["artifact_id", "created_at", "artifact_path"]


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


class RecallArtifact(BaseModel):
    artifact_id: str
    query: str
    signal_ids: list[str] = Field(default_factory=list)
    markdown_text: str
    artifact_path: str | None = None
    graph_paths: dict[str, list[str]] = Field(default_factory=dict)
    provenance_contract: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
