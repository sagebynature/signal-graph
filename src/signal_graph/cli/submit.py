from __future__ import annotations

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.raw_items import create_manual_raw_item, persist_raw_item
from signal_graph.storage.sqlite import SqliteStore


def submit(text: str = typer.Option(..., "--text")) -> None:
    raw_item = create_manual_raw_item(text=text)
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    persist_raw_item(store, raw_item)
    print(raw_item.model_dump_json())
