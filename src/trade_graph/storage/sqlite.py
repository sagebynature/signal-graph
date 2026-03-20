from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from trade_graph.models.events import EventCandidate
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
