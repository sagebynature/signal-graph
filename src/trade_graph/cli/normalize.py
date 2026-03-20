from __future__ import annotations

import typer

from trade_graph.config import DEFAULT_PROJECT_DIR
from trade_graph.services.normalize import normalize_and_persist_raw_item
from trade_graph.storage.sqlite import SqliteStore


def normalize(raw_item: str = typer.Option(..., "--raw-item")) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "trade_graph.db")
    event_candidate = normalize_and_persist_raw_item(store, raw_item)
    print(event_candidate.model_dump_json())
