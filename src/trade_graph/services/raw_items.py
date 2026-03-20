from __future__ import annotations

from uuid import uuid4

from trade_graph.models.source import RawSourceItem
from trade_graph.storage.sqlite import SqliteStore


def create_manual_raw_item(text: str) -> RawSourceItem:
    return RawSourceItem(
        raw_item_id=f"raw-{uuid4().hex}",
        source_tier="tier3_manual",
        source_name="manual",
        raw_text=text,
    )


def persist_raw_item(store: SqliteStore, raw_item: RawSourceItem) -> RawSourceItem:
    store.init_db()
    store.insert_raw_source_item(raw_item)
    return raw_item
