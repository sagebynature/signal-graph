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


def merge_event_candidates(
    existing: EventCandidate,
    incoming: EventCandidate,
) -> EventCandidate:
    return EventCandidate(
        event_candidate_id=existing.event_candidate_id,
        title=incoming.title,
        event_type=incoming.event_type
        if incoming.event_type != "unknown"
        else existing.event_type,
        direction=incoming.direction
        if incoming.direction != "unknown"
        else existing.direction,
        primary_entities=incoming.primary_entities or existing.primary_entities,
        dedupe_fingerprint=incoming.dedupe_fingerprint or existing.dedupe_fingerprint,
        secondary_entities=incoming.secondary_entities or existing.secondary_entities,
        source_item_ids=sorted(
            set(existing.source_item_ids + incoming.source_item_ids)
        ),
        candidate_confidence=max(
            existing.candidate_confidence, incoming.candidate_confidence
        ),
        candidate_status=(
            incoming.candidate_status
            if incoming.candidate_status != "pending"
            else existing.candidate_status
        ),
        created_at=existing.created_at,
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

    event_candidate = normalize_raw_item(
        raw_item,
        event_type=event_type,
        direction=direction,
        primary_entities=primary_entities,
        secondary_entities=secondary_entities,
    )
    existing_event_candidate = store.get_event_candidate_for_raw_item(raw_item_id)
    if existing_event_candidate is not None:
        event_candidate = merge_event_candidates(
            existing_event_candidate,
            event_candidate,
        )
        store.update_event_candidate(event_candidate)
        return event_candidate

    store.insert_event_candidate(event_candidate)
    return event_candidate
