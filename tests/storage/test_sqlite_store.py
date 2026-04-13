from __future__ import annotations

from datetime import datetime

from signal_graph.models.journal import RecallArtifact, RecallQuery
from signal_graph.services.journal import create_journal_signal
from signal_graph.storage.sqlite import SqliteStore


def test_sqlite_store_initializes_journal_schema_and_round_trips_signals(tmp_path):
    store = SqliteStore(tmp_path / ".signal-graph" / "signal_graph.db")
    store.init_db()

    assert store.table_exists("journal_signals")
    assert store.table_exists("recall_artifacts")

    signal = create_journal_signal(
        text="Direct storage signal",
        origin_type="user",
        source_name="manual",
        what_refs=["storage"],
    )
    store.save_journal_signal(signal)

    persisted = store.get_journal_signal(signal.signal_id)
    assert persisted is not None
    assert persisted.signal_id == signal.signal_id
    assert persisted.what_refs == ["storage"]


def test_sqlite_store_persists_recall_artifacts(tmp_path):
    store = SqliteStore(tmp_path / ".signal-graph" / "signal_graph.db")
    store.init_db()

    artifact_path = tmp_path / "artifact.md"
    artifact_path.write_text("# artifact")
    artifact = RecallArtifact(
        artifact_id="ra-test",
        query="storage",
        signal_ids=["sig-1"],
        view="ranked",
        query_contract=RecallQuery(raw_query="storage", tokens=["storage"]),
        matches=[],
        session_groups=[],
        markdown_text=artifact_path.read_text(),
        artifact_path=str(artifact_path),
        graph_paths={"sig-1": ["SIGNAL", "WHAT"]},
        provenance_contract={"required_fields": ["signal_id"]},
        created_at=datetime.fromisoformat("2026-04-13T00:00:00+00:00"),
    )

    store.save_recall_artifact(artifact)

    db_path = tmp_path / ".signal-graph" / "signal_graph.db"
    assert db_path.is_file()
    assert artifact_path.read_text() == "# artifact"
