from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import re
import sqlite3
from pathlib import Path

from signal_graph.models.events import EventCandidate
from signal_graph.models.graph import GraphEvent
from signal_graph.models.journal import JournalSignal, RecallArtifact
from signal_graph.models.policy import ScoringPolicy
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
            self._insert_event_candidate(connection, event_candidate)

    def update_event_candidate(self, event_candidate: EventCandidate) -> None:
        with self._connect() as connection:
            self._update_event_candidate(connection, event_candidate)

    def get_event_candidate_for_raw_item(
        self, raw_item_id: str
    ) -> EventCandidate | None:
        with self._connect() as connection:
            return self._get_event_candidate_for_raw_item(connection, raw_item_id)

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

        return self._hydrate_event_candidate(row)

    def event_candidate_has_downstream_artifacts(self, event_candidate_id: str) -> bool:
        with self._connect() as connection:
            return self._event_candidate_has_downstream_artifacts(
                connection, event_candidate_id
            )

    def split_legacy_event_candidate_for_raw_item(
        self,
        existing_event_candidate: EventCandidate,
        new_event_candidate: EventCandidate,
        *,
        raw_item_id: str,
    ) -> EventCandidate:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current_event_candidate = self._get_event_candidate_for_raw_item(
                connection, raw_item_id
            )
            if current_event_candidate is None:
                raise ValueError(f"raw item mapping not found: {raw_item_id}")
            if (
                current_event_candidate.event_candidate_id
                != existing_event_candidate.event_candidate_id
            ):
                return current_event_candidate
            if len(current_event_candidate.source_item_ids) <= 1:
                return current_event_candidate
            if self._event_candidate_has_downstream_artifacts(
                connection, current_event_candidate.event_candidate_id
            ):
                raise ValueError(
                    "processed legacy candidates cannot be auto-split because research bundles or graph events already exist"
                )

            peeled_source_item_ids = [
                source_item_id
                for source_item_id in current_event_candidate.source_item_ids
                if source_item_id != raw_item_id
            ]
            self._update_event_candidate(
                connection,
                EventCandidate(
                    event_candidate_id=current_event_candidate.event_candidate_id,
                    title=current_event_candidate.title,
                    event_type=current_event_candidate.event_type,
                    direction=current_event_candidate.direction,
                    primary_entities=current_event_candidate.primary_entities,
                    dedupe_fingerprint=current_event_candidate.dedupe_fingerprint,
                    secondary_entities=current_event_candidate.secondary_entities,
                    source_item_ids=peeled_source_item_ids,
                    candidate_confidence=current_event_candidate.candidate_confidence,
                    candidate_status=current_event_candidate.candidate_status,
                    created_at=current_event_candidate.created_at,
                ),
            )
            self._insert_event_candidate(connection, new_event_candidate)
            return new_event_candidate

    def save_research_bundle(self, bundle: ResearchBundle) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO research_bundles (
                    research_bundle_id,
                    event_candidate_id,
                    bundle_revision,
                    scoring_policy_snapshot,
                    supporting_documents,
                    contradictions,
                    entity_resolution_results,
                    evidence_spans,
                    research_confidence,
                    research_notes,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bundle.research_bundle_id,
                    bundle.event_candidate_id,
                    bundle.bundle_revision,
                    json.dumps(bundle.scoring_policy_snapshot.model_dump(mode="json"))
                    if bundle.scoring_policy_snapshot is not None
                    else None,
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
                    scoring_policy_snapshot,
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
            scoring_policy_snapshot=(
                ScoringPolicy.model_validate(json.loads(row[3])) if row[3] else None
            ),
            supporting_documents=json.loads(row[4]),
            contradictions=json.loads(row[5]),
            entity_resolution_results=json.loads(row[6]) if row[6] else None,
            evidence_spans=json.loads(row[7]),
            research_confidence=row[8],
            research_notes=row[9],
            created_at=datetime.fromisoformat(row[10]) if row[10] else None,
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

    def get_research_bundle_by_id(
        self, research_bundle_id: str
    ) -> ResearchBundle | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    research_bundle_id,
                    event_candidate_id,
                    bundle_revision,
                    scoring_policy_snapshot,
                    supporting_documents,
                    contradictions,
                    entity_resolution_results,
                    evidence_spans,
                    research_confidence,
                    research_notes,
                    created_at
                FROM research_bundles
                WHERE research_bundle_id = ?
                """,
                (research_bundle_id,),
            ).fetchone()

        if row is None:
            return None

        return ResearchBundle(
            research_bundle_id=row[0],
            event_candidate_id=row[1],
            bundle_revision=row[2] or 1,
            scoring_policy_snapshot=(
                ScoringPolicy.model_validate(json.loads(row[3])) if row[3] else None
            ),
            supporting_documents=json.loads(row[4]),
            contradictions=json.loads(row[5]),
            entity_resolution_results=json.loads(row[6]) if row[6] else None,
            evidence_spans=json.loads(row[7]),
            research_confidence=row[8],
            research_notes=row[9],
            created_at=datetime.fromisoformat(row[10]) if row[10] else None,
        )

    def save_graph_event(self, graph_event: GraphEvent) -> None:
        research_bundle_id = graph_event.research_bundle_id
        if research_bundle_id is None:
            raise ValueError(
                f"graph event missing bound research bundle: {graph_event.graph_event_id}"
            )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO graph_events (
                    graph_event_id,
                    event_candidate_id,
                    research_bundle_id,
                    committed_at,
                    trust_score,
                    eligible_modes,
                    ingest_decision
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    graph_event.graph_event_id,
                    graph_event.event_candidate_id,
                    research_bundle_id,
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
                    research_bundle_id,
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
            research_bundle_id=row[2],
            committed_at=datetime.fromisoformat(row[3]) if row[3] else None,
            trust_score=row[4],
            eligible_modes=json.loads(row[5]),
            ingest_decision=row[6],
        )

    def save_journal_signal(self, signal: JournalSignal) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO journal_signals (
                    signal_id,
                    origin_type,
                    source_name,
                    source_url,
                    source_ref,
                    raw_text,
                    raw_payload,
                    content_hash,
                    captured_at,
                    observed_at,
                    published_at,
                    agent_host,
                    agent_process,
                    agent_runtime,
                    agent_session_id,
                    agent_role,
                    workspace_path,
                    intent_status,
                    why_text,
                    who_refs,
                    what_refs,
                    where_refs,
                    how_refs,
                    graph_path,
                    journaled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._serialize_journal_signal(signal),
            )

    def get_journal_signal(self, signal_id: str) -> JournalSignal | None:
        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT {self._journal_signal_select_columns()}
                FROM journal_signals
                WHERE signal_id = ?
                """,
                (signal_id,),
            ).fetchone()

        return self._hydrate_journal_signal(row)

    def list_journal_signals(self) -> list[JournalSignal]:
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._journal_signal_select_columns()}
                FROM journal_signals
                ORDER BY captured_at DESC, signal_id DESC
                """
            ).fetchall()

        return [
            signal
            for row in rows
            if (signal := self._hydrate_journal_signal(row)) is not None
        ]

    def search_journal_signals(
        self,
        query: str,
        *,
        limit: int = 5,
        origin_type: str | None = None,
        session_id: str | None = None,
        runtime_family: str | None = None,
        source_name: str | None = None,
    ) -> list[JournalSignal]:
        query_terms = self._query_terms(query)
        exact_phrases = self._query_phrases(query)
        scored: list[tuple[int, JournalSignal]] = []
        for signal in self.list_journal_signals():
            if origin_type is not None and signal.origin_type != origin_type:
                continue
            if session_id is not None and signal.agent_session_id != session_id:
                continue
            if runtime_family is not None and signal.agent_runtime != runtime_family:
                continue
            if source_name is not None and signal.source_name != source_name:
                continue

            score = self._journal_signal_score(
                signal, query_terms=query_terms, exact_phrases=exact_phrases
            )
            if query.strip() and score <= 0:
                continue
            scored.append((score, signal))

        scored.sort(
            key=lambda item: (
                item[0],
                item[1].captured_at.isoformat() if item[1].captured_at else "",
                item[1].signal_id,
            ),
            reverse=True,
        )
        return [signal for _, signal in scored[:limit]]

    def save_recall_artifact(self, artifact: RecallArtifact) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO recall_artifacts (
                    artifact_id,
                    query,
                    signal_ids,
                    markdown_text,
                    artifact_path,
                    graph_paths,
                    provenance_contract,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._serialize_recall_artifact(artifact),
            )

    def _apply_additive_migrations(self, connection: sqlite3.Connection) -> None:
        self._ensure_column(connection, "event_candidates", "dedupe_fingerprint TEXT")
        self._ensure_column(connection, "event_candidates", "created_at TEXT")
        self._ensure_column(connection, "research_bundles", "bundle_revision INTEGER")
        self._ensure_column(
            connection, "research_bundles", "scoring_policy_snapshot TEXT"
        )
        self._ensure_column(connection, "research_bundles", "created_at TEXT")
        self._ensure_column(connection, "graph_events", "research_bundle_id TEXT")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS event_candidate_source_items (
                raw_item_id TEXT PRIMARY KEY REFERENCES raw_source_items(raw_item_id) ON DELETE CASCADE,
                event_candidate_id TEXT NOT NULL REFERENCES event_candidates(event_candidate_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_event_candidates_dedupe_fingerprint
                ON event_candidates(dedupe_fingerprint)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_event_candidate_source_items_event_candidate_id
                ON event_candidate_source_items(event_candidate_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_research_bundles_event_candidate_revision
                ON research_bundles(event_candidate_id, bundle_revision DESC, created_at DESC)
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_research_bundles_event_candidate_revision_unique
                ON research_bundles(event_candidate_id, bundle_revision)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_signals (
                signal_id TEXT PRIMARY KEY,
                origin_type TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT,
                source_ref TEXT,
                raw_text TEXT NOT NULL,
                raw_payload TEXT,
                content_hash TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                observed_at TEXT,
                published_at TEXT,
                agent_host TEXT,
                agent_process TEXT,
                agent_runtime TEXT,
                agent_session_id TEXT,
                agent_role TEXT,
                workspace_path TEXT,
                intent_status TEXT NOT NULL,
                why_text TEXT,
                who_refs TEXT NOT NULL,
                what_refs TEXT NOT NULL,
                where_refs TEXT NOT NULL,
                how_refs TEXT NOT NULL,
                graph_path TEXT NOT NULL DEFAULT '[]',
                journaled_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recall_artifacts (
                artifact_id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                signal_ids TEXT NOT NULL,
                markdown_text TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                graph_paths TEXT NOT NULL,
                provenance_contract TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._ensure_column(connection, "journal_signals", "source_url TEXT")
        self._ensure_column(connection, "journal_signals", "source_ref TEXT")
        self._ensure_column(connection, "journal_signals", "raw_payload TEXT")
        self._ensure_column(connection, "journal_signals", "observed_at TEXT")
        self._ensure_column(connection, "journal_signals", "published_at TEXT")
        self._ensure_column(connection, "journal_signals", "agent_host TEXT")
        self._ensure_column(connection, "journal_signals", "agent_process TEXT")
        self._ensure_column(connection, "journal_signals", "agent_runtime TEXT")
        self._ensure_column(connection, "journal_signals", "agent_session_id TEXT")
        self._ensure_column(connection, "journal_signals", "agent_role TEXT")
        self._ensure_column(connection, "journal_signals", "workspace_path TEXT")
        self._ensure_column(connection, "journal_signals", "why_text TEXT")
        self._ensure_column(connection, "journal_signals", "graph_path TEXT")
        self._ensure_column(connection, "journal_signals", "journaled_at TEXT")
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_journal_signals_captured_at
                ON journal_signals(captured_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_journal_signals_session_id
                ON journal_signals(agent_session_id)
            """
        )
        self._backfill_event_candidate_provenance(connection)
        self._backfill_event_candidate_source_item_lookup(connection)
        self._backfill_research_bundle_provenance(connection)
        self._backfill_graph_event_research_bundle_lookup(connection)
        self._backfill_journal_signal_defaults(connection)

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
            WHERE dedupe_fingerprint IS NULL
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

    def _backfill_event_candidate_source_item_lookup(
        self, connection: sqlite3.Connection
    ) -> None:
        connection.execute("DELETE FROM event_candidate_source_items")
        rows = connection.execute(
            """
            SELECT event_candidate_id, source_item_ids
            FROM event_candidates
            ORDER BY
                CASE WHEN created_at IS NULL THEN 1 ELSE 0 END,
                created_at,
                event_candidate_id
            """
        ).fetchall()
        for event_candidate_id, source_item_ids in rows:
            for raw_item_id in json.loads(source_item_ids):
                if not self._raw_source_item_exists(connection, raw_item_id):
                    continue
                connection.execute(
                    """
                    INSERT OR IGNORE INTO event_candidate_source_items (
                        raw_item_id,
                        event_candidate_id
                    ) VALUES (?, ?)
                    """,
                    (raw_item_id, event_candidate_id),
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

    def _backfill_graph_event_research_bundle_lookup(
        self, connection: sqlite3.Connection
    ) -> None:
        connection.execute(
            """
            UPDATE graph_events
            SET research_bundle_id = (
                SELECT research_bundle_id
                FROM research_bundles
                WHERE research_bundles.event_candidate_id = graph_events.event_candidate_id
                ORDER BY bundle_revision DESC, created_at DESC, rowid DESC
                LIMIT 1
            )
            WHERE research_bundle_id IS NULL
            """
        )

    def _set_event_candidate_source_items(
        self,
        connection: sqlite3.Connection,
        event_candidate_id: str,
        source_item_ids: list[str],
    ) -> None:
        connection.execute(
            """
            DELETE FROM event_candidate_source_items
            WHERE event_candidate_id = ?
            """,
            (event_candidate_id,),
        )
        for raw_item_id in source_item_ids:
            if not self._raw_source_item_exists(connection, raw_item_id):
                continue
            connection.execute(
                """
                INSERT INTO event_candidate_source_items (
                    raw_item_id,
                    event_candidate_id
                ) VALUES (?, ?)
                ON CONFLICT(raw_item_id) DO UPDATE
                SET event_candidate_id = excluded.event_candidate_id
                """,
                (raw_item_id, event_candidate_id),
            )

    def _raw_source_item_exists(
        self, connection: sqlite3.Connection, raw_item_id: str
    ) -> bool:
        row = connection.execute(
            """
            SELECT 1
            FROM raw_source_items
            WHERE raw_item_id = ?
            """,
            (raw_item_id,),
        ).fetchone()
        return row is not None

    def _get_event_candidate_for_raw_item(
        self, connection: sqlite3.Connection, raw_item_id: str
    ) -> EventCandidate | None:
        row = connection.execute(
            """
            SELECT
                ec.event_candidate_id,
                ec.title,
                ec.event_type,
                ec.direction,
                ec.primary_entities,
                ec.dedupe_fingerprint,
                ec.secondary_entities,
                ec.source_item_ids,
                ec.candidate_confidence,
                ec.candidate_status,
                ec.created_at
            FROM event_candidate_source_items AS ecsi
            JOIN event_candidates AS ec
                ON ec.event_candidate_id = ecsi.event_candidate_id
            WHERE ecsi.raw_item_id = ?
            """,
            (raw_item_id,),
        ).fetchone()
        return self._hydrate_event_candidate(row)

    def _insert_event_candidate(
        self, connection: sqlite3.Connection, event_candidate: EventCandidate
    ) -> None:
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
        self._set_event_candidate_source_items(
            connection,
            event_candidate.event_candidate_id,
            event_candidate.source_item_ids,
        )

    def _update_event_candidate(
        self, connection: sqlite3.Connection, event_candidate: EventCandidate
    ) -> None:
        connection.execute(
            """
            UPDATE event_candidates
            SET title = ?,
                event_type = ?,
                direction = ?,
                primary_entities = ?,
                dedupe_fingerprint = ?,
                secondary_entities = ?,
                source_item_ids = ?,
                candidate_confidence = ?,
                candidate_status = ?,
                created_at = ?
            WHERE event_candidate_id = ?
            """,
            (
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
                event_candidate.event_candidate_id,
            ),
        )
        self._set_event_candidate_source_items(
            connection,
            event_candidate.event_candidate_id,
            event_candidate.source_item_ids,
        )

    def _event_candidate_has_downstream_artifacts(
        self, connection: sqlite3.Connection, event_candidate_id: str
    ) -> bool:
        research_bundle_row = connection.execute(
            """
            SELECT 1
            FROM research_bundles
            WHERE event_candidate_id = ?
            LIMIT 1
            """,
            (event_candidate_id,),
        ).fetchone()
        graph_event_row = connection.execute(
            """
            SELECT 1
            FROM graph_events
            WHERE event_candidate_id = ?
            LIMIT 1
            """,
            (event_candidate_id,),
        ).fetchone()
        return research_bundle_row is not None or graph_event_row is not None

    def _hydrate_event_candidate(
        self, row: sqlite3.Row | tuple | None
    ) -> EventCandidate | None:
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

    def _backfill_journal_signal_defaults(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            UPDATE journal_signals
            SET graph_path = '[]'
            WHERE graph_path IS NULL OR graph_path = ''
            """
        )

    def _hydrate_journal_signal(
        self, row: sqlite3.Row | tuple | None
    ) -> JournalSignal | None:
        if row is None:
            return None

        return JournalSignal(
            signal_id=row[0],
            origin_type=row[1],
            source_name=row[2],
            source_url=row[3],
            source_ref=row[4],
            raw_text=row[5],
            raw_payload=row[6],
            content_hash=row[7],
            captured_at=datetime.fromisoformat(row[8]) if row[8] else None,
            observed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            published_at=datetime.fromisoformat(row[10]) if row[10] else None,
            agent_host=row[11],
            agent_process=row[12],
            agent_runtime=row[13],
            agent_session_id=row[14],
            agent_role=row[15],
            workspace_path=row[16],
            intent_status=row[17],
            why_text=row[18],
            who_refs=json.loads(row[19]),
            what_refs=json.loads(row[20]),
            where_refs=json.loads(row[21]),
            how_refs=json.loads(row[22]),
            graph_path=json.loads(row[23]),
            journaled_at=datetime.fromisoformat(row[24]) if row[24] else None,
        )

    def _journal_signal_score(
        self,
        signal: JournalSignal,
        *,
        query_terms: list[str],
        exact_phrases: list[str],
    ) -> int:
        if not query_terms and not exact_phrases:
            return 1

        score = 0
        raw_text = signal.raw_text.lower()
        source_fields = [
            (signal.source_name or "").lower(),
            (signal.source_ref or "").lower(),
            (signal.source_url or "").lower(),
            (signal.workspace_path or "").lower(),
            (signal.origin_type or "").lower(),
            (signal.agent_runtime or "").lower(),
            (signal.agent_session_id or "").lower(),
            (signal.agent_process or "").lower(),
        ]
        taxonomy_fields = {
            "who": [ref.lower() for ref in signal.who_refs],
            "what": [ref.lower() for ref in signal.what_refs],
            "where": [ref.lower() for ref in signal.where_refs],
            "how": [ref.lower() for ref in signal.how_refs],
            "why": [(signal.why_text or "").lower()],
        }

        for phrase in exact_phrases:
            if phrase in raw_text:
                score += 10
            elif any(phrase in value for value in source_fields):
                score += 6
            elif any(
                phrase in value
                for values in taxonomy_fields.values()
                for value in values
            ):
                score += 5

        for term in query_terms:
            if term in raw_text:
                score += 5
            if any(term in value for value in taxonomy_fields["what"]):
                score += 4
            if any(term in value for value in source_fields):
                score += 3
            if any(
                term in value
                for field in ("who", "where", "how", "why")
                for value in taxonomy_fields[field]
            ):
                score += 2
        return score

    def _query_terms(self, query: str) -> list[str]:
        return re.findall(r"[a-z0-9_:-]+", query.lower())

    def _query_phrases(self, query: str) -> list[str]:
        return [phrase.lower() for phrase in re.findall(r'"([^"]+)"', query)]

    def _journal_signal_select_columns(self) -> str:
        return """
            signal_id,
            origin_type,
            source_name,
            source_url,
            source_ref,
            raw_text,
            raw_payload,
            content_hash,
            captured_at,
            observed_at,
            published_at,
            agent_host,
            agent_process,
            agent_runtime,
            agent_session_id,
            agent_role,
            workspace_path,
            intent_status,
            why_text,
            who_refs,
            what_refs,
            where_refs,
            how_refs,
            graph_path,
            journaled_at
        """

    def _serialize_journal_signal(self, signal: JournalSignal) -> tuple:
        return (
            signal.signal_id,
            signal.origin_type,
            signal.source_name,
            signal.source_url,
            signal.source_ref,
            signal.raw_text,
            signal.raw_payload,
            signal.content_hash,
            signal.captured_at.isoformat() if signal.captured_at else "",
            signal.observed_at.isoformat() if signal.observed_at else None,
            signal.published_at.isoformat() if signal.published_at else None,
            signal.agent_host,
            signal.agent_process,
            signal.agent_runtime,
            signal.agent_session_id,
            signal.agent_role,
            signal.workspace_path,
            signal.intent_status,
            signal.why_text,
            json.dumps(signal.who_refs),
            json.dumps(signal.what_refs),
            json.dumps(signal.where_refs),
            json.dumps(signal.how_refs),
            json.dumps(signal.graph_path),
            signal.journaled_at.isoformat() if signal.journaled_at else None,
        )

    def _serialize_recall_artifact(self, artifact: RecallArtifact) -> tuple:
        return (
            artifact.artifact_id,
            artifact.query,
            json.dumps(artifact.signal_ids),
            artifact.markdown_text,
            artifact.artifact_path or "",
            json.dumps(artifact.graph_paths),
            json.dumps(artifact.provenance_contract),
            artifact.created_at.isoformat() if artifact.created_at else "",
        )
