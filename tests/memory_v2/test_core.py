from __future__ import annotations

from datetime import UTC, datetime

import pytest

from signal_graph.memory_v2 import CapturePolicy, FileMemoryStore, MemoryService


def _service(tmp_path):
    return MemoryService(
        store=FileMemoryStore(tmp_path / "memory-v2"),
        policy=CapturePolicy(),
    )


def test_owner_email_is_unique_and_name_is_retrievable(tmp_path):
    service = _service(tmp_path)

    owner = service.create_owner(email="sage@example.com", display_name="Sage")

    assert owner.email == "sage@example.com"
    assert service.get_owner_by_email("sage@example.com").display_name == "Sage"

    with pytest.raises(ValueError, match="already exists"):
        service.create_owner(email="sage@example.com", display_name="Someone Else")


def test_actor_and_event_persistence_require_explicit_owner_link(tmp_path):
    service = _service(tmp_path)

    with pytest.raises(ValueError, match="owner"):
        service.register_actor(
            owner_email="missing@example.com",
            runtime_family="codex",
            host="machine-a",
            session_id="session-1",
        )

    service.create_owner(email="sage@example.com", display_name="Sage")
    actor = service.register_actor(
        owner_email="sage@example.com",
        runtime_family="codex",
        host="machine-a",
        session_id="session-1",
    )

    with pytest.raises(ValueError, match="owner"):
        service.capture_hook_event(
            owner_email="other@example.com",
            actor_id=actor.actor_id,
            phase="pre_action",
            action_text="Plan the rewrite",
            observed_facts=["opened the workspace"],
            topic_refs=["rewrite"],
            occurred_at=datetime(2026, 4, 12, 12, 0, tzinfo=UTC),
        )


def test_policy_requires_confirmation_for_inferred_why_but_auto_captures_observable_facts(
    tmp_path,
):
    service = _service(tmp_path)
    service.create_owner(email="sage@example.com", display_name="Sage")
    actor = service.register_actor(
        owner_email="sage@example.com",
        runtime_family="codex",
        host="machine-a",
        session_id="session-1",
    )

    unconfirmed = service.capture_hook_event(
        owner_email="sage@example.com",
        actor_id=actor.actor_id,
        phase="post_output",
        action_text="Chose approach-x",
        observed_facts=["updated the rollout plan"],
        topic_refs=["approach-x"],
        inferred_why="Approach-x seemed safer.",
        why_confidence=0.83,
        confirmed=False,
        occurred_at=datetime(2026, 4, 12, 12, 1, tzinfo=UTC),
    )

    assert unconfirmed.observed_facts == ["updated the rollout plan"]
    assert unconfirmed.why_inference is None
    assert unconfirmed.pending_why is not None
    assert unconfirmed.pending_why.reason == "confirmation_required"

    confirmed = service.capture_hook_event(
        owner_email="sage@example.com",
        actor_id=actor.actor_id,
        phase="post_output",
        action_text="Chose approach-x again",
        observed_facts=["updated the rollout plan again"],
        topic_refs=["approach-x"],
        inferred_why="Approach-x preserves provenance.",
        why_confidence=0.91,
        confirmed=True,
        occurred_at=datetime(2026, 4, 12, 12, 2, tzinfo=UTC),
    )

    assert confirmed.why_inference is not None
    assert confirmed.why_inference.text == "Approach-x preserves provenance."
    assert confirmed.why_inference.confidence == pytest.approx(0.91)
