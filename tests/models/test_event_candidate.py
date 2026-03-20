from __future__ import annotations

from signal_graph.models.events import EventCandidate


def test_event_candidate_defaults():
    event = EventCandidate(
        event_candidate_id="evt-1",
        title="NVDA supplier disruption",
        event_type="supply_disruption",
        direction="negative",
        primary_entities=["NVDA"],
    )

    assert event.candidate_status == "pending"
