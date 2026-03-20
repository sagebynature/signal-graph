from __future__ import annotations

import typer

from trade_graph.config import DEFAULT_PROJECT_DIR
from trade_graph.services.raw_items import create_manual_raw_item, persist_raw_item
from trade_graph.storage.sqlite import SqliteStore


def submit(text: str = typer.Option(..., "--text")) -> None:
    raw_item = create_manual_raw_item(text=text)
    store = SqliteStore(DEFAULT_PROJECT_DIR / "trade_graph.db")
    persist_raw_item(store, raw_item)
    print(raw_item.model_dump_json())
