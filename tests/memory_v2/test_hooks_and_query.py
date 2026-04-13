from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from signal_graph.memory_v2 import CapturePolicy, FileMemoryStore, MemoryService


def _service(tmp_path):
    return MemoryService(
        store=FileMemoryStore(tmp_path / "memory-v2"),
        policy=CapturePolicy(),
    )


def test_hook_capture_supports_target_runtimes_and_query_by_who_topic_date(tmp_path):
    service = _service(tmp_path)
    service.create_owner(email="sage@example.com", display_name="Sage")

    runtimes = ("claude-code", "opencode", "gemini", "codex")
    linked_event_ids: list[str] = []

    for runtime in runtimes:
        actor = service.register_actor(
            owner_email="sage@example.com",
            runtime_family=runtime,
            host=f"{runtime}-host",
            session_id=f"{runtime}-session",
        )
        pre = service.capture_hook_event(
            owner_email="sage@example.com",
            actor_id=actor.actor_id,
            phase="pre_action",
            action_text=f"{runtime} planned deployment review",
            observed_facts=[f"{runtime} opened the plan"],
            topic_refs=["deployment"],
            occurred_at=datetime(2026, 4, 11, 9, 0, tzinfo=UTC),
        )
        post = service.capture_hook_event(
            owner_email="sage@example.com",
            actor_id=actor.actor_id,
            phase="post_output",
            action_text=f"{runtime} updated the deployment checklist",
            observed_facts=[f"{runtime} wrote the checklist update"],
            topic_refs=["deployment"],
            parent_event_id=pre.event_id,
            occurred_at=datetime(2026, 4, 11, 9, 5, tzinfo=UTC),
            evidence_refs=[f"{runtime}/deployment.md"],
        )
        assert post.parent_event_id == pre.event_id
        assert post.runtime_family == runtime
        linked_event_ids.extend([pre.event_id, post.event_id])

    result = service.query(
        owner_email="sage@example.com",
        topic="deployment",
        on_date=date(2026, 4, 11),
    )

    assert len(result.events) == 8
    assert {event.runtime_family for event in result.events} == set(runtimes)
    assert {event.event_id for event in result.events} == set(linked_event_ids)


def test_redaction_hides_targeted_event_and_marks_explanation(tmp_path):
    service = _service(tmp_path)
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
        observed_facts=["recorded approach-x in the plan"],
        topic_refs=["approach-x"],
        occurred_at=datetime(2026, 4, 12, 13, 0, tzinfo=UTC),
        evidence_refs=["notes/decision.md"],
    )

    redaction = service.record_redaction(
        owner_email="sage@example.com",
        target_id=event.event_id,
        reason="contains sensitive secret material",
    )
    duplicate = service.record_redaction(
        owner_email="sage@example.com",
        target_id=event.event_id,
        reason="contains sensitive secret material",
    )
    query = service.query(owner_email="sage@example.com", topic="approach-x")
    explanation = service.explain_action(event.event_id)
    layout = service.store.describe_layout()

    assert duplicate.redaction_id == redaction.redaction_id
    assert query.events == []
    assert query.applied_redactions[0].target_id == event.event_id
    assert explanation.is_redacted is True
    assert explanation.action_text == "[redacted]"
    assert explanation.provenance_chain == []
    assert explanation.evidence_refs == []
    assert explanation.active_redactions[0].redaction_id == redaction.redaction_id
    assert explanation.guidance == ["Redacted: contains sensitive secret material"]
    assert Path(layout["redactions"]).is_dir()
