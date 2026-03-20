from __future__ import annotations

from datetime import datetime, UTC

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import (
    REFERENCE_GRAPH_QUERIES,
    SCHEMA_CONSTRAINTS,
    graph_cleanup_query,
    graph_event_params,
    graph_event_query,
)
from signal_graph.models.graph import GraphEvent
from signal_graph.storage.sqlite import SqliteStore


def _ingest_event_candidate(store: SqliteStore, event_candidate_id: str) -> GraphEvent:
    event_candidate = store.get_event_candidate(event_candidate_id)
    if event_candidate is None:
        raise ValueError(f"event candidate not found: {event_candidate_id}")

    bundle = store.get_research_bundle(event_candidate_id)
    if bundle is None:
        raise ValueError(f"research bundle not found: {event_candidate_id}")

    client = GraphClient()
    try:
        for constraint in SCHEMA_CONSTRAINTS:
            client.run(constraint)
        for query in REFERENCE_GRAPH_QUERIES:
            client.run(query)
        params = graph_event_params(event_candidate, bundle)
        client.run(graph_cleanup_query(), params)
        client.run(
            graph_event_query(),
            params,
        )
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    graph_event = GraphEvent(
        graph_event_id=f"ge-{event_candidate.event_candidate_id}",
        event_candidate_id=event_candidate.event_candidate_id,
        research_bundle_id=bundle.research_bundle_id,
        committed_at=datetime.now(UTC),
        ingest_decision="committed",
    )
    store.save_graph_event(graph_event)
    return graph_event


def ingest(
    event_candidate: str = typer.Option(
        ...,
        "--event-candidate",
        help="Event candidate id to ingest into the graph.",
    ),
) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    graph_event = _ingest_event_candidate(store, event_candidate)
    print(graph_event.model_dump_json())
