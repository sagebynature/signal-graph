from __future__ import annotations

from datetime import UTC, datetime

from signal_graph.memory_v2 import CapturePolicy, FileMemoryStore, MemoryService


class FakeGraphBoundary:
    def __init__(self) -> None:
        self.batches: list[list[tuple[str, dict[str, object] | None]]] = []

    def project(self, statements: list[tuple[str, dict[str, object] | None]]) -> None:
        self.batches.append(statements)


def _service(tmp_path, graph_boundary: FakeGraphBoundary) -> MemoryService:
    return MemoryService(
        store=FileMemoryStore(tmp_path / "memory-v2"),
        policy=CapturePolicy(),
        graph_boundary=graph_boundary,
    )


def test_memory_events_project_owner_actor_and_event_edges_to_graph_boundary(tmp_path):
    boundary = FakeGraphBoundary()
    service = _service(tmp_path, boundary)
    service.create_owner(email="sage@example.com", display_name="Sage")
    actor = service.register_actor(
        owner_email="sage@example.com",
        runtime_family="codex",
        host="machine-a",
        session_id="session-1",
    )

    event = service.capture_hook_event(
        owner_email="sage@example.com",
        actor_id=actor.actor_id,
        phase="post_output",
        action_text="Selected approach-x",
        observed_facts=["wrote the decision note"],
        topic_refs=["approach-x"],
        occurred_at=datetime(2026, 4, 12, 16, 0, tzinfo=UTC),
        inferred_why="Approach-x preserves provenance.",
        why_confidence=0.8,
        confirmed=True,
        evidence_refs=["notes/decision.md"],
    )

    assert boundary.batches
    statements = boundary.batches[-1]
    rendered = "\n".join(statement for statement, _ in statements).lower()
    params = [payload for _, payload in statements if payload]

    assert "merge (owner:memoryowner" in rendered
    assert "merge (actor:memoryactor" in rendered
    assert "merge (event:memoryevent" in rendered
    assert "merge (owner)-[:owns]->(actor)" in rendered
    assert "merge (actor)-[:acted_in]->(event)" in rendered
    assert any(payload.get("event_id") == event.event_id for payload in params)
    assert any(payload.get("owner_email") == "sage@example.com" for payload in params)


def test_artifact_and_correction_projection_include_owner_scoped_links(tmp_path):
    boundary = FakeGraphBoundary()
    service = _service(tmp_path, boundary)
    service.create_owner(email="sage@example.com", display_name="Sage")
    actor = service.register_actor(
        owner_email="sage@example.com",
        runtime_family="gemini",
        host="machine-b",
        session_id="session-2",
    )
    event = service.capture_hook_event(
        owner_email="sage@example.com",
        actor_id=actor.actor_id,
        phase="post_output",
        action_text="Shared approach-x summary",
        observed_facts=["prepared the artifact share"],
        topic_refs=["approach-x"],
        occurred_at=datetime(2026, 4, 12, 16, 10, tzinfo=UTC),
    )
    source = tmp_path / "shared.md"
    source.write_text("approach-x summary")
    artifact = service.share_artifact(
        owner_email="sage@example.com",
        actor_id=actor.actor_id,
        source_path=source,
        title="Shared summary",
        topic_refs=["approach-x"],
        occurred_at=datetime(2026, 4, 12, 16, 12, tzinfo=UTC),
    )
    service.record_correction(
        owner_email="sage@example.com",
        target_id=event.event_id,
        topic="approach-x",
        instruction="Do not use approach-x by default.",
    )

    rendered = "\n".join(
        statement for batch in boundary.batches for statement, _ in batch
    ).lower()

    assert "merge (artifact:memoryartifact" in rendered
    assert "merge (event)-[:generated_artifact]->(artifact)" in rendered
    assert "merge (correction:memorycorrection" in rendered
    assert "merge (owner)-[:issued]->(correction)" in rendered
    assert artifact.artifact_id in str(boundary.batches)
