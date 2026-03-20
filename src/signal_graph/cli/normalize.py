from __future__ import annotations

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.normalize import normalize_and_persist_raw_item
from signal_graph.storage.sqlite import SqliteStore


def normalize(raw_item: str = typer.Option(..., "--raw-item")) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    event_candidate = normalize_and_persist_raw_item(store, raw_item)
    print(event_candidate.model_dump_json())
