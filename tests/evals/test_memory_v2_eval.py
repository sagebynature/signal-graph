from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from signal_graph.memory_v2 import CapturePolicy, FileMemoryStore, MemoryService


def _service(tmp_path):
    return MemoryService(
        store=FileMemoryStore(tmp_path / "memory-v2"),
        policy=CapturePolicy(),
    )


def test_cross_device_explanation_and_correction_eval(tmp_path):
    service = _service(tmp_path)
    service.create_owner(email="sage@example.com", display_name="Sage")

    codex = service.register_actor(
        owner_email="sage@example.com",
        runtime_family="codex",
        host="machine-a",
        session_id="session-a",
    )
    claude = service.register_actor(
        owner_email="sage@example.com",
        runtime_family="claude-code",
        host="machine-b",
        session_id="session-b",
    )

    pre = service.capture_hook_event(
        owner_email="sage@example.com",
        actor_id=codex.actor_id,
        phase="pre_action",
        action_text="Evaluate approach-x",
        observed_facts=["opened the decision brief"],
        topic_refs=["approach-x"],
        occurred_at=datetime(2026, 4, 12, 14, 0, tzinfo=UTC),
    )
    decision = service.capture_hook_event(
        owner_email="sage@example.com",
        actor_id=codex.actor_id,
        phase="post_output",
        action_text="Chose approach-x",
        observed_facts=["recorded approach-x in the plan"],
        topic_refs=["approach-x"],
        parent_event_id=pre.event_id,
        occurred_at=datetime(2026, 4, 12, 14, 5, tzinfo=UTC),
        inferred_why="Approach-x preserves provenance across machines.",
        why_confidence=0.84,
        confirmed=True,
        evidence_refs=["notes/machine-a.md"],
    )
    service.capture_hook_event(
        owner_email="sage@example.com",
        actor_id=claude.actor_id,
        phase="post_output",
        action_text="Reviewed approach-x",
        observed_facts=["confirmed the plan on the second machine"],
        topic_refs=["approach-x"],
        parent_event_id=decision.event_id,
        occurred_at=datetime(2026, 4, 12, 14, 8, tzinfo=UTC),
        evidence_refs=["notes/machine-b.md"],
    )

    explanation_before = service.explain_action(decision.event_id)

    assert explanation_before.owner.email == "sage@example.com"
    assert explanation_before.actor.runtime_family == "codex"
    assert explanation_before.action_text == "Chose approach-x"
    assert explanation_before.provenance_chain == [pre.event_id, decision.event_id]
    assert explanation_before.evidence_refs == ["notes/machine-a.md"]
    assert explanation_before.why_inference is not None
    assert explanation_before.why_inference.confidence == 0.84
    assert explanation_before.guidance == []

    correction = service.record_correction(
        owner_email="sage@example.com",
        target_id=decision.event_id,
        topic="approach-x",
        instruction="Do not choose approach-x in the future.",
    )
    explanation_after = service.explain_action(decision.event_id)
    query_after = service.query(owner_email="sage@example.com", topic="approach-x")

    assert (
        explanation_after.active_corrections[0].correction_id
        == correction.correction_id
    )
    assert explanation_after.guidance == ["Do not choose approach-x in the future."]
    assert query_after.guidance == ["Do not choose approach-x in the future."]


def test_artifact_share_eval_preserves_raw_artifact_and_separates_derived_memory(
    tmp_path,
):
    service = _service(tmp_path)
    service.create_owner(email="sage@example.com", display_name="Sage")
    actor = service.register_actor(
        owner_email="sage@example.com",
        runtime_family="gemini",
        host="machine-c",
        session_id="session-c",
    )

    source_artifact = tmp_path / "shared" / "decision-note.md"
    source_artifact.parent.mkdir(parents=True, exist_ok=True)
    source_artifact.write_text("# Decision\nApproach-x preserves auditability.\n")

    artifact = service.share_artifact(
        owner_email="sage@example.com",
        actor_id=actor.actor_id,
        source_path=source_artifact,
        title="Decision note",
        topic_refs=["approach-x", "auditability"],
        occurred_at=datetime(2026, 4, 12, 15, 0, tzinfo=UTC),
    )
    derived = service.derive_artifact_memory(
        owner_email="sage@example.com",
        artifact_id=artifact.artifact_id,
        source_event_id=artifact.share_event_id,
        summary="Approach-x is currently favored for auditability.",
        topics=["approach-x", "auditability"],
        confidence=0.73,
    )

    before = service.query(owner_email="sage@example.com", topic="approach-x")
    canonical_raw = Path(artifact.canonical_raw_path)

    assert canonical_raw.read_text() == source_artifact.read_text()
    assert before.artifacts[0].artifact_id == artifact.artifact_id
    assert (
        before.derived_interpretations[0].interpretation_id == derived.interpretation_id
    )

    service.record_correction(
        owner_email="sage@example.com",
        target_id=derived.interpretation_id,
        topic="approach-x",
        instruction="Treat approach-x as deprecated guidance.",
    )
    after = service.query(owner_email="sage@example.com", topic="approach-x")
    layout = service.store.describe_layout()

    assert canonical_raw.read_text() == source_artifact.read_text()
    assert after.derived_interpretations == []
    assert after.guidance == ["Treat approach-x as deprecated guidance."]
    assert Path(layout["artifacts_raw"]).is_dir()
    assert Path(layout["derived"]).is_dir()
    assert Path(layout["views_markdown"]).is_dir()
