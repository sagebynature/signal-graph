from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from trade_graph.models.events import EventCandidate
from trade_graph.models.graph import GraphEvent
from trade_graph.models.research import ResearchBundle
from trade_graph.models.source import RawSourceItem


class SqliteStore:
    def __init__(self, path: Path):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def init_db(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            schema_sql = Path(__file__).with_name("schema.sql").read_text()
            connection.executescript(schema_sql)

    def table_exists(self, name: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (name,),
            )
            return cursor.fetchone() is not None

    def insert_raw_source_item(self, raw_item: RawSourceItem) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO raw_source_items (
                    raw_item_id,
                    source_tier,
                    source_name,
                    source_url,
                    fetched_at,
                    published_at,
                    raw_text,
                    raw_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    raw_item.raw_item_id,
                    raw_item.source_tier,
                    raw_item.source_name,
                    raw_item.source_url,
                    raw_item.fetched_at.isoformat() if raw_item.fetched_at else None,
                    raw_item.published_at.isoformat() if raw_item.published_at else None,
                    raw_item.raw_text,
                    raw_item.raw_payload,
                ),
            )

    def get_raw_source_item(self, raw_item_id: str) -> RawSourceItem | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    raw_item_id,
                    source_tier,
                    source_name,
                    source_url,
                    fetched_at,
                    published_at,
                    raw_text,
                    raw_payload
                FROM raw_source_items
                WHERE raw_item_id = ?
                """,
                (raw_item_id,),
            ).fetchone()

        if row is None:
            return None

        return RawSourceItem(
            raw_item_id=row[0],
            source_tier=row[1],
            source_name=row[2],
            source_url=row[3],
            fetched_at=row[4],
            published_at=row[5],
            raw_text=row[6],
            raw_payload=row[7],
        )

    def insert_event_candidate(self, event_candidate: EventCandidate) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO event_candidates (
                    event_candidate_id,
                    title,
                    event_type,
                    direction,
                    primary_entities,
                    secondary_entities,
                    source_item_ids,
                    candidate_confidence,
                    candidate_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_candidate.event_candidate_id,
                    event_candidate.title,
                    event_candidate.event_type,
                    event_candidate.direction,
                    json.dumps(event_candidate.primary_entities),
                    json.dumps(event_candidate.secondary_entities),
                    json.dumps(event_candidate.source_item_ids),
                    event_candidate.candidate_confidence,
                    event_candidate.candidate_status,
                ),
            )

    def get_event_candidate(self, event_candidate_id: str) -> EventCandidate | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    event_candidate_id,
                    title,
                    event_type,
                    direction,
                    primary_entities,
                    secondary_entities,
                    source_item_ids,
                    candidate_confidence,
                    candidate_status
                FROM event_candidates
                WHERE event_candidate_id = ?
                """,
                (event_candidate_id,),
            ).fetchone()

        if row is None:
            return None

        return EventCandidate(
            event_candidate_id=row[0],
            title=row[1],
            event_type=row[2],
            direction=row[3],
            primary_entities=json.loads(row[4]),
            secondary_entities=json.loads(row[5]),
            source_item_ids=json.loads(row[6]),
            candidate_confidence=row[7],
            candidate_status=row[8],
        )

    def save_research_bundle(self, bundle: ResearchBundle) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO research_bundles (
                    research_bundle_id,
                    event_candidate_id,
                    supporting_documents,
                    contradictions,
                    entity_resolution_results,
                    evidence_spans,
                    research_confidence,
                    research_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bundle.research_bundle_id,
                    bundle.event_candidate_id,
                    json.dumps(bundle.supporting_documents),
                    json.dumps(bundle.contradictions),
                    json.dumps(bundle.entity_resolution_results)
                    if bundle.entity_resolution_results is not None
                    else None,
                    json.dumps(bundle.evidence_spans),
                    bundle.research_confidence,
                    bundle.research_notes,
                ),
            )

    def get_research_bundle(self, event_candidate_id: str) -> ResearchBundle | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    research_bundle_id,
                    event_candidate_id,
                    supporting_documents,
                    contradictions,
                    entity_resolution_results,
                    evidence_spans,
                    research_confidence,
                    research_notes
                FROM research_bundles
                WHERE event_candidate_id = ?
                """,
                (event_candidate_id,),
            ).fetchone()

        if row is None:
            return None

        return ResearchBundle(
            research_bundle_id=row[0],
            event_candidate_id=row[1],
            supporting_documents=json.loads(row[2]),
            contradictions=json.loads(row[3]),
            entity_resolution_results=json.loads(row[4]) if row[4] else None,
            evidence_spans=json.loads(row[5]),
            research_confidence=row[6],
            research_notes=row[7],
        )

    def save_graph_event(self, graph_event: GraphEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO graph_events (
                    graph_event_id,
                    event_candidate_id,
                    committed_at,
                    trust_score,
                    eligible_modes,
                    ingest_decision
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    graph_event.graph_event_id,
                    graph_event.event_candidate_id,
                    graph_event.committed_at.isoformat()
                    if graph_event.committed_at is not None
                    else "",
                    graph_event.trust_score,
                    json.dumps(graph_event.eligible_modes),
                    graph_event.ingest_decision,
                ),
            )
