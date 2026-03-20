from __future__ import annotations

from trade_graph.models.events import EventCandidate
from trade_graph.models.research import ResearchBundle
from trade_graph.storage.sqlite import SqliteStore


def build_research_bundle(event: EventCandidate) -> ResearchBundle:
    return ResearchBundle(
        research_bundle_id=f"rb-{event.event_candidate_id}",
        event_candidate_id=event.event_candidate_id,
        supporting_documents=[],
        contradictions=[],
        research_confidence=0.0,
    )


def build_and_persist_research_bundle(
    store: SqliteStore,
    event_candidate_id: str,
) -> ResearchBundle:
    event_candidate = store.get_event_candidate(event_candidate_id)
    if event_candidate is None:
        raise ValueError(f"event candidate not found: {event_candidate_id}")

    bundle = build_research_bundle(event_candidate)
    store.save_research_bundle(bundle)
    return bundle
