from __future__ import annotations

import sqlite3

from signal_graph.models.events import EventCandidate
from signal_graph.models.research import ResearchBundle
from signal_graph.storage.sqlite import SqliteStore


def test_init_db_creates_canonical_pipeline_tables(tmp_path):
    store = SqliteStore(tmp_path / "signal_graph.db")

    store.init_db()

    assert store.table_exists("raw_source_items")
    assert store.table_exists("event_candidates")
    assert store.table_exists("event_candidate_source_items")
    assert store.table_exists("research_bundles")
    assert store.table_exists("graph_events")


def test_init_db_adds_foreign_keys_for_related_event_tables(tmp_path):
    store = SqliteStore(tmp_path / "signal_graph.db")

    store.init_db()

    with sqlite3.connect(tmp_path / "signal_graph.db") as connection:
        research_bundle_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(research_bundles)"
        ).fetchall()
        graph_event_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(graph_events)"
        ).fetchall()

    assert any(row[2] == "event_candidates" for row in research_bundle_foreign_keys)
    assert any(row[2] == "event_candidates" for row in graph_event_foreign_keys)


def test_init_db_adds_provenance_columns_for_event_and_research_tables(tmp_path):
    store = SqliteStore(tmp_path / "signal_graph.db")

    store.init_db()

    with sqlite3.connect(tmp_path / "signal_graph.db") as connection:
        event_candidate_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(event_candidates)")
        }
        research_bundle_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(research_bundles)")
        }

    assert {"dedupe_fingerprint", "created_at"} <= event_candidate_columns
    assert {"bundle_revision", "created_at"} <= research_bundle_columns


def test_get_research_bundle_returns_latest_revision_for_event_candidate(tmp_path):
    store = SqliteStore(tmp_path / "signal_graph.db")
    store.init_db()
    event_candidate = EventCandidate(
        event_candidate_id="evt-123",
        title="NVDA supplier disruption",
        event_type="supplier_disruption",
        direction="negative",
        primary_entities=["NVDA"],
        dedupe_fingerprint="fp-123",
        source_item_ids=["raw-1"],
    )
    first_bundle = ResearchBundle(
        research_bundle_id="rb-evt-123",
        event_candidate_id=event_candidate.event_candidate_id,
        bundle_revision=1,
        supporting_documents=["https://example.com/1"],
        research_notes="first revision",
    )
    second_bundle = ResearchBundle(
        research_bundle_id="rb-evt-123-r0002",
        event_candidate_id=event_candidate.event_candidate_id,
        bundle_revision=2,
        supporting_documents=["https://example.com/2"],
        research_notes="second revision",
    )

    store.insert_event_candidate(event_candidate)
    store.save_research_bundle(first_bundle)
    store.save_research_bundle(second_bundle)

    latest_bundle = store.get_research_bundle(event_candidate.event_candidate_id)

    assert latest_bundle is not None
    assert latest_bundle.research_bundle_id == second_bundle.research_bundle_id
    assert latest_bundle.supporting_documents == ["https://example.com/2"]
    assert latest_bundle.research_notes == "second revision"


def test_init_db_preserves_existing_rows_while_adding_provenance_columns(tmp_path):
    database_path = tmp_path / "signal_graph.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE raw_source_items (
                raw_item_id TEXT PRIMARY KEY,
                source_tier TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT,
                fetched_at TEXT,
                published_at TEXT,
                raw_text TEXT NOT NULL,
                raw_payload TEXT
            );

            CREATE TABLE event_candidates (
                event_candidate_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                primary_entities TEXT NOT NULL,
                secondary_entities TEXT NOT NULL,
                source_item_ids TEXT NOT NULL,
                candidate_confidence REAL NOT NULL,
                candidate_status TEXT NOT NULL
            );

            CREATE TABLE research_bundles (
                research_bundle_id TEXT PRIMARY KEY,
                event_candidate_id TEXT NOT NULL REFERENCES event_candidates(event_candidate_id) ON DELETE CASCADE,
                supporting_documents TEXT NOT NULL,
                contradictions TEXT NOT NULL,
                entity_resolution_results TEXT,
                evidence_spans TEXT,
                research_confidence REAL NOT NULL,
                research_notes TEXT
            );

            INSERT INTO event_candidates (
                event_candidate_id,
                title,
                event_type,
                direction,
                primary_entities,
                secondary_entities,
                source_item_ids,
                candidate_confidence,
                candidate_status
            ) VALUES (
                'evt-legacy',
                'Legacy event title',
                'unknown',
                'unknown',
                '["NVDA"]',
                '[]',
                '["raw-1"]',
                0.0,
                'pending'
            );

            INSERT INTO research_bundles (
                research_bundle_id,
                event_candidate_id,
                supporting_documents,
                contradictions,
                entity_resolution_results,
                evidence_spans,
                research_confidence,
                research_notes
            ) VALUES (
                'rb-legacy',
                'evt-legacy',
                '["https://example.com/legacy"]',
                '[]',
                NULL,
                '[]',
                0.3,
                'legacy row'
            );
            """
        )

    store = SqliteStore(database_path)
    store.init_db()

    with sqlite3.connect(database_path) as connection:
        event_row = connection.execute(
            """
            SELECT dedupe_fingerprint, created_at
            FROM event_candidates
            WHERE event_candidate_id = 'evt-legacy'
            """
        ).fetchone()
        research_row = connection.execute(
            """
            SELECT bundle_revision, created_at
            FROM research_bundles
            WHERE research_bundle_id = 'rb-legacy'
            """
        ).fetchone()

    assert event_row is not None
    assert event_row[0]
    assert event_row[1] is None
    assert research_row == (1, None)


def test_init_db_backfills_raw_item_event_lookup_rows_for_existing_candidates(tmp_path):
    database_path = tmp_path / "signal_graph.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE raw_source_items (
                raw_item_id TEXT PRIMARY KEY,
                source_tier TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT,
                fetched_at TEXT,
                published_at TEXT,
                raw_text TEXT NOT NULL,
                raw_payload TEXT
            );

            CREATE TABLE event_candidates (
                event_candidate_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                primary_entities TEXT NOT NULL,
                secondary_entities TEXT NOT NULL,
                source_item_ids TEXT NOT NULL,
                candidate_confidence REAL NOT NULL,
                candidate_status TEXT NOT NULL
            );

            INSERT INTO raw_source_items (
                raw_item_id,
                source_tier,
                source_name,
                raw_text
            ) VALUES
                ('raw-1', 'manual', 'test', 'NVDA supplier disruption'),
                ('raw-2', 'manual', 'test', 'NVDA supplier disruption');

            INSERT INTO event_candidates (
                event_candidate_id,
                title,
                event_type,
                direction,
                primary_entities,
                secondary_entities,
                source_item_ids,
                candidate_confidence,
                candidate_status
            ) VALUES (
                'evt-legacy',
                'NVDA supplier disruption',
                'unknown',
                'unknown',
                '[]',
                '[]',
                '["raw-1", "raw-2"]',
                0.0,
                'pending'
            );
            """
        )

    store = SqliteStore(database_path)
    store.init_db()

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT raw_item_id, event_candidate_id
            FROM event_candidate_source_items
            ORDER BY raw_item_id
            """
        ).fetchall()

    assert rows == [("raw-1", "evt-legacy"), ("raw-2", "evt-legacy")]
