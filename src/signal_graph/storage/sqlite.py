from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import sqlite3
from pathlib import Path

from signal_graph.models.events import EventCandidate
from signal_graph.models.graph import GraphEvent
from signal_graph.models.research import ResearchBundle
from signal_graph.models.source import RawSourceItem


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
            self._apply_additive_migrations(connection)

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
                INSERT OR REPLACE INTO raw_source_items (
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
                    raw_item.published_at.isoformat()
                    if raw_item.published_at
                    else None,
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
                INSERT INTO event_candidates (
                    event_candidate_id,
                    title,
                    event_type,
                    direction,
                    primary_entities,
                    dedupe_fingerprint,
                    secondary_entities,
                    source_item_ids,
                    candidate_confidence,
                    candidate_status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_candidate.event_candidate_id,
                    event_candidate.title,
                    event_candidate.event_type,
                    event_candidate.direction,
                    json.dumps(event_candidate.primary_entities),
                    event_candidate.dedupe_fingerprint,
                    json.dumps(event_candidate.secondary_entities),
                    json.dumps(event_candidate.source_item_ids),
                    event_candidate.candidate_confidence,
                    event_candidate.candidate_status,
                    event_candidate.created_at.isoformat()
                    if event_candidate.created_at is not None
                    else None,
                ),
            )

    def get_event_candidate_for_raw_item(
        self, raw_item_id: str
    ) -> EventCandidate | None:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    event_candidate_id,
                    title,
                    event_type,
                    direction,
                    primary_entities,
                    dedupe_fingerprint,
                    secondary_entities,
                    source_item_ids,
                    candidate_confidence,
                    candidate_status,
                    created_at
                FROM event_candidates
                ORDER BY created_at DESC, rowid DESC
                """
            ).fetchall()

        for row in rows:
            event_candidate = EventCandidate(
                event_candidate_id=row[0],
                title=row[1],
                event_type=row[2],
                direction=row[3],
                primary_entities=json.loads(row[4]),
                dedupe_fingerprint=row[5],
                secondary_entities=json.loads(row[6]),
                source_item_ids=json.loads(row[7]),
                candidate_confidence=row[8],
                candidate_status=row[9],
                created_at=datetime.fromisoformat(row[10]) if row[10] else None,
            )
            if raw_item_id in event_candidate.source_item_ids:
                return event_candidate

        return None

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
                    dedupe_fingerprint,
                    secondary_entities,
                    source_item_ids,
                    candidate_confidence,
                    candidate_status,
                    created_at
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
            dedupe_fingerprint=row[5],
            secondary_entities=json.loads(row[6]),
            source_item_ids=json.loads(row[7]),
            candidate_confidence=row[8],
            candidate_status=row[9],
            created_at=datetime.fromisoformat(row[10]) if row[10] else None,
        )

    def save_research_bundle(self, bundle: ResearchBundle) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO research_bundles (
                    research_bundle_id,
                    event_candidate_id,
                    bundle_revision,
                    supporting_documents,
                    contradictions,
                    entity_resolution_results,
                    evidence_spans,
                    research_confidence,
                    research_notes,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bundle.research_bundle_id,
                    bundle.event_candidate_id,
                    bundle.bundle_revision,
                    json.dumps(bundle.supporting_documents),
                    json.dumps(bundle.contradictions),
                    json.dumps(bundle.entity_resolution_results)
                    if bundle.entity_resolution_results is not None
                    else None,
                    json.dumps(bundle.evidence_spans),
                    bundle.research_confidence,
                    bundle.research_notes,
                    bundle.created_at.isoformat()
                    if bundle.created_at is not None
                    else None,
                ),
            )

    def get_research_bundle(self, event_candidate_id: str) -> ResearchBundle | None:
        return self.get_latest_research_bundle(event_candidate_id)

    def get_latest_research_bundle(
        self, event_candidate_id: str
    ) -> ResearchBundle | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    research_bundle_id,
                    event_candidate_id,
                    bundle_revision,
                    supporting_documents,
                    contradictions,
                    entity_resolution_results,
                    evidence_spans,
                    research_confidence,
                    research_notes,
                    created_at
                FROM research_bundles
                WHERE event_candidate_id = ?
                ORDER BY bundle_revision DESC, created_at DESC, rowid DESC
                LIMIT 1
                """,
                (event_candidate_id,),
            ).fetchone()

        if row is None:
            return None

        return ResearchBundle(
            research_bundle_id=row[0],
            event_candidate_id=row[1],
            bundle_revision=row[2] or 1,
            supporting_documents=json.loads(row[3]),
            contradictions=json.loads(row[4]),
            entity_resolution_results=json.loads(row[5]) if row[5] else None,
            evidence_spans=json.loads(row[6]),
            research_confidence=row[7],
            research_notes=row[8],
            created_at=datetime.fromisoformat(row[9]) if row[9] else None,
        )

    def next_research_bundle_revision(self, event_candidate_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(MAX(bundle_revision), 0) + 1
                FROM research_bundles
                WHERE event_candidate_id = ?
                """,
                (event_candidate_id,),
            ).fetchone()

        return int(row[0]) if row is not None else 1

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

    def get_graph_event(self, graph_event_id: str) -> GraphEvent | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    graph_event_id,
                    event_candidate_id,
                    committed_at,
                    trust_score,
                    eligible_modes,
                    ingest_decision
                FROM graph_events
                WHERE graph_event_id = ?
                """,
                (graph_event_id,),
            ).fetchone()

        if row is None:
            return None

        return GraphEvent(
            graph_event_id=row[0],
            event_candidate_id=row[1],
            committed_at=datetime.fromisoformat(row[2]) if row[2] else None,
            trust_score=row[3],
            eligible_modes=json.loads(row[4]),
            ingest_decision=row[5],
        )

    def _apply_additive_migrations(self, connection: sqlite3.Connection) -> None:
        self._ensure_column(connection, "event_candidates", "dedupe_fingerprint TEXT")
        self._ensure_column(connection, "event_candidates", "created_at TEXT")
        self._ensure_column(connection, "research_bundles", "bundle_revision INTEGER")
        self._ensure_column(connection, "research_bundles", "created_at TEXT")
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_event_candidates_dedupe_fingerprint
                ON event_candidates(dedupe_fingerprint)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_research_bundles_event_candidate_revision
                ON research_bundles(event_candidate_id, bundle_revision DESC, created_at DESC)
            """
        )
        self._backfill_event_candidate_provenance(connection)
        self._backfill_research_bundle_provenance(connection)

    def _ensure_column(
        self, connection: sqlite3.Connection, table_name: str, column_definition: str
    ) -> None:
        column_name = column_definition.split()[0]
        existing_columns = {
            row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")
        }
        if column_name in existing_columns:
            return

        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")

    def _backfill_event_candidate_provenance(
        self, connection: sqlite3.Connection
    ) -> None:
        rows = connection.execute(
            """
            SELECT event_candidate_id, title
            FROM event_candidates
            WHERE dedupe_fingerprint IS NULL OR created_at IS NULL
            """
        ).fetchall()
        for event_candidate_id, title in rows:
            normalized_title = (title or "").strip().lower()
            connection.execute(
                """
                UPDATE event_candidates
                SET dedupe_fingerprint = COALESCE(dedupe_fingerprint, ?)
                WHERE event_candidate_id = ?
                """,
                (
                    sha256(normalized_title.encode()).hexdigest(),
                    event_candidate_id,
                ),
            )

    def _backfill_research_bundle_provenance(
        self, connection: sqlite3.Connection
    ) -> None:
        connection.execute(
            """
            UPDATE research_bundles
            SET bundle_revision = (
                SELECT COUNT(*)
                FROM research_bundles AS prior_revisions
                WHERE prior_revisions.event_candidate_id = research_bundles.event_candidate_id
                  AND prior_revisions.rowid <= research_bundles.rowid
            )
            WHERE bundle_revision IS NULL
            """
        )
