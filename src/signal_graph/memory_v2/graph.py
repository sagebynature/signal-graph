from __future__ import annotations

from typing import Protocol

from signal_graph.graph.client import GraphClient
from signal_graph.memory_v2.models import (
    Actor,
    ArtifactShare,
    Correction,
    MemoryEvent,
    Owner,
    Redaction,
)


type Statement = tuple[str, dict[str, object] | None]


class MemoryGraphBoundary(Protocol):
    def project(self, statements: list[Statement]) -> None: ...


class NoOpMemoryGraphBoundary:
    def project(self, statements: list[Statement]) -> None:
        _ = statements


class Neo4jMemoryGraphBoundary:
    def __init__(self, client: GraphClient | None = None) -> None:
        self._client = client

    def project(self, statements: list[Statement]) -> None:
        client = self._client or GraphClient()
        close = self._client is None
        try:
            client.run_in_transaction(statements)
        finally:
            if close:
                client.close()


def event_projection_statements(
    *, owner: Owner, actor: Actor, event: MemoryEvent
) -> list[Statement]:
    return [
        (
            "MERGE (owner:MemoryOwner {owner_id: $owner_id}) "
            "SET owner.email = $owner_email, owner.display_name = $display_name",
            {
                "owner_id": owner.owner_id,
                "owner_email": owner.email,
                "display_name": owner.display_name,
            },
        ),
        (
            "MERGE (actor:MemoryActor {actor_id: $actor_id}) "
            "SET actor.runtime_family = $runtime_family, actor.host = $host, actor.session_id = $session_id",
            {
                "actor_id": actor.actor_id,
                "runtime_family": actor.runtime_family,
                "host": actor.host,
                "session_id": actor.session_id,
            },
        ),
        (
            "MERGE (event:MemoryEvent {event_id: $event_id}) "
            "SET event.phase = $phase, event.action_text = $action_text, event.occurred_at = $occurred_at, "
            "event.topic_refs = $topic_refs, event.evidence_refs = $evidence_refs",
            {
                "event_id": event.event_id,
                "phase": event.phase,
                "action_text": event.action_text,
                "occurred_at": event.occurred_at.isoformat(),
                "topic_refs": event.topic_refs,
                "evidence_refs": event.evidence_refs,
            },
        ),
        (
            "MATCH (owner:MemoryOwner {owner_id: $owner_id}) "
            "MATCH (actor:MemoryActor {actor_id: $actor_id}) "
            "MERGE (owner)-[:OWNS]->(actor)",
            {"owner_id": owner.owner_id, "actor_id": actor.actor_id},
        ),
        (
            "MATCH (actor:MemoryActor {actor_id: $actor_id}) "
            "MATCH (event:MemoryEvent {event_id: $event_id}) "
            "MERGE (actor)-[:ACTED_IN]->(event)",
            {"actor_id": actor.actor_id, "event_id": event.event_id},
        ),
    ]


def artifact_projection_statements(
    *, owner: Owner, event: MemoryEvent, artifact: ArtifactShare
) -> list[Statement]:
    return [
        (
            "MERGE (artifact:MemoryArtifact {artifact_id: $artifact_id}) "
            "SET artifact.title = $title, artifact.canonical_raw_path = $canonical_raw_path, artifact.sha256 = $sha256",
            {
                "artifact_id": artifact.artifact_id,
                "title": artifact.title,
                "canonical_raw_path": artifact.canonical_raw_path,
                "sha256": artifact.sha256,
            },
        ),
        (
            "MATCH (owner:MemoryOwner {owner_id: $owner_id}) "
            "MATCH (artifact:MemoryArtifact {artifact_id: $artifact_id}) "
            "MERGE (owner)-[:OWNS_ARTIFACT]->(artifact)",
            {"owner_id": owner.owner_id, "artifact_id": artifact.artifact_id},
        ),
        (
            "MATCH (event:MemoryEvent {event_id: $event_id}) "
            "MATCH (artifact:MemoryArtifact {artifact_id: $artifact_id}) "
            "MERGE (event)-[:GENERATED_ARTIFACT]->(artifact)",
            {"event_id": event.event_id, "artifact_id": artifact.artifact_id},
        ),
    ]


def correction_projection_statements(
    *, owner: Owner, correction: Correction
) -> list[Statement]:
    return [
        (
            "MERGE (correction:MemoryCorrection {correction_id: $correction_id}) "
            "SET correction.target_id = $target_id, correction.topic = $topic, correction.instruction = $instruction, "
            "correction.created_at = $created_at",
            {
                "correction_id": correction.correction_id,
                "target_id": correction.target_id,
                "topic": correction.topic,
                "instruction": correction.instruction,
                "created_at": correction.created_at.isoformat(),
            },
        ),
        (
            "MATCH (owner:MemoryOwner {owner_id: $owner_id}) "
            "MATCH (correction:MemoryCorrection {correction_id: $correction_id}) "
            "MERGE (owner)-[:ISSUED]->(correction)",
            {"owner_id": owner.owner_id, "correction_id": correction.correction_id},
        ),
    ]


def redaction_projection_statements(
    *, owner: Owner, redaction: Redaction
) -> list[Statement]:
    return [
        (
            "MERGE (redaction:MemoryRedaction {redaction_id: $redaction_id}) "
            "SET redaction.target_id = $target_id, redaction.reason = $reason, "
            "redaction.created_at = $created_at",
            {
                "redaction_id": redaction.redaction_id,
                "target_id": redaction.target_id,
                "reason": redaction.reason,
                "created_at": redaction.created_at.isoformat(),
            },
        ),
        (
            "MATCH (owner:MemoryOwner {owner_id: $owner_id}) "
            "MATCH (redaction:MemoryRedaction {redaction_id: $redaction_id}) "
            "MERGE (owner)-[:ISSUED]->(redaction)",
            {"owner_id": owner.owner_id, "redaction_id": redaction.redaction_id},
        ),
    ]
