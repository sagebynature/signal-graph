from __future__ import annotations

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.normalize import normalize_and_persist_raw_item
from signal_graph.storage.sqlite import SqliteStore


def normalize(
    raw_item: str = typer.Option(..., "--raw-item"),
    event_type: str | None = typer.Option(None, "--event-type"),
    direction: str | None = typer.Option(None, "--direction"),
    primary_entity: list[str] | None = typer.Option(None, "--primary-entity"),
    secondary_entity: list[str] | None = typer.Option(None, "--secondary-entity"),
) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    event_candidate = normalize_and_persist_raw_item(
        store,
        raw_item,
        event_type=event_type,
        direction=direction,
        primary_entities=primary_entity or [],
        secondary_entities=secondary_entity or [],
    )
    print(event_candidate.model_dump_json())
