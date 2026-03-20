from __future__ import annotations

from datetime import datetime, UTC

import typer

from trade_graph.config import DEFAULT_PROJECT_DIR
from trade_graph.graph.client import GraphClient
from trade_graph.graph.schema import SCHEMA_CONSTRAINTS, graph_event_query
from trade_graph.models.graph import GraphEvent
from trade_graph.storage.sqlite import SqliteStore


def _ingest_event_candidate(store: SqliteStore, event_candidate_id: str) -> GraphEvent:
    event_candidate = store.get_event_candidate(event_candidate_id)
    if event_candidate is None:
        raise ValueError(f"event candidate not found: {event_candidate_id}")

    bundle = store.get_research_bundle(event_candidate_id)
    if bundle is None:
        raise ValueError(f"research bundle not found: {event_candidate_id}")

    client = GraphClient()
    for constraint in SCHEMA_CONSTRAINTS:
        client.run(constraint)
    client.run(
        graph_event_query(),
        {
            "event_candidate_id": event_candidate.event_candidate_id,
            "research_bundle_id": bundle.research_bundle_id,
        },
    )

    graph_event = GraphEvent(
        graph_event_id=f"ge-{event_candidate.event_candidate_id}",
        event_candidate_id=event_candidate.event_candidate_id,
        committed_at=datetime.now(UTC),
        ingest_decision="committed",
    )
    store.save_graph_event(graph_event)
    return graph_event


def ingest(event_candidate: str = typer.Option(..., "--event-candidate")) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "trade_graph.db")
    graph_event = _ingest_event_candidate(store, event_candidate)
    print(graph_event.model_dump_json())
