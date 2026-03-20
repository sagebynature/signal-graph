from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from signal_graph.models.events import EventCandidate
from signal_graph.models.source import RawSourceItem
from signal_graph.storage.sqlite import SqliteStore


def normalize_raw_item(
    raw_item: RawSourceItem,
    *,
    event_type: str | None = None,
    direction: str | None = None,
    primary_entities: list[str] | None = None,
    secondary_entities: list[str] | None = None,
) -> EventCandidate:
    normalized_title = raw_item.raw_text.strip()
    fingerprint = sha256(normalized_title.lower().encode()).hexdigest()
    return EventCandidate(
        event_candidate_id=f"evt-{uuid4().hex[:12]}",
        title=normalized_title,
        event_type=event_type or "unknown",
        direction=direction or "unknown",
        primary_entities=primary_entities or [],
        dedupe_fingerprint=fingerprint,
        secondary_entities=secondary_entities or [],
        source_item_ids=[raw_item.raw_item_id],
        created_at=datetime.now(UTC),
    )


def normalize_and_persist_raw_item(
    store: SqliteStore,
    raw_item_id: str,
    *,
    event_type: str | None = None,
    direction: str | None = None,
    primary_entities: list[str] | None = None,
    secondary_entities: list[str] | None = None,
) -> EventCandidate:
    raw_item = store.get_raw_source_item(raw_item_id)
    if raw_item is None:
        raise ValueError(f"raw item not found: {raw_item_id}")

    existing_event_candidate = store.get_event_candidate_for_raw_item(raw_item_id)
    if existing_event_candidate is not None:
        return existing_event_candidate

    event_candidate = normalize_raw_item(
        raw_item,
        event_type=event_type,
        direction=direction,
        primary_entities=primary_entities,
        secondary_entities=secondary_entities,
    )
    store.insert_event_candidate(event_candidate)
    return event_candidate
