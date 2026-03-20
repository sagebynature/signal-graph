from __future__ import annotations

import sqlite3

from signal_graph.storage.sqlite import SqliteStore


def test_init_db_creates_canonical_pipeline_tables(tmp_path):
    store = SqliteStore(tmp_path / "signal_graph.db")

    store.init_db()

    assert store.table_exists("raw_source_items")
    assert store.table_exists("event_candidates")
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
