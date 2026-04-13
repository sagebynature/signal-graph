from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from signal_graph.models.journal import JournalSignal, RecallArtifact

_JOURNAL_SIGNAL_SELECT = """
    SELECT
        signal_id,
        origin_type,
        source_name,
        source_url,
        source_ref,
        raw_text,
        raw_payload,
        content_hash,
        observed_at,
        published_at,
        captured_at,
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
    FROM journal_signals
"""


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
            row = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (name,),
            ).fetchone()
        return row is not None

    def save_journal_signal(self, signal: JournalSignal) -> None:
        payload = signal.model_dump(mode="json")
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
                    observed_at,
                    published_at,
                    captured_at,
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
                (
                    payload["signal_id"],
                    payload["origin_type"],
                    payload["source_name"],
                    payload["source_url"],
                    payload["source_ref"],
                    payload["raw_text"],
                    payload["raw_payload"],
                    payload["content_hash"],
                    payload["observed_at"],
                    payload["published_at"],
                    payload["captured_at"],
                    payload["agent_host"],
                    payload["agent_process"],
                    payload["agent_runtime"],
                    payload["agent_session_id"],
                    payload["agent_role"],
                    payload["workspace_path"],
                    payload["intent_status"],
                    payload["why_text"],
                    _encode(payload["who_refs"]),
                    _encode(payload["what_refs"]),
                    _encode(payload["where_refs"]),
                    _encode(payload["how_refs"]),
                    _encode(payload["graph_path"]),
                    payload["journaled_at"],
                ),
            )

    def get_journal_signal(self, signal_id: str) -> JournalSignal | None:
        with self._connect() as connection:
            row = connection.execute(
                f"{_JOURNAL_SIGNAL_SELECT} WHERE signal_id = ?",
                (signal_id,),
            ).fetchone()
        if row is None:
            return None
        return _hydrate_journal_signal(row)

    def list_journal_signals(self) -> list[JournalSignal]:
        with self._connect() as connection:
            rows = connection.execute(
                f"{_JOURNAL_SIGNAL_SELECT} ORDER BY captured_at DESC, signal_id DESC"
            ).fetchall()
        return [_hydrate_journal_signal(row) for row in rows]

    def save_recall_artifact(self, artifact: RecallArtifact) -> None:
        payload = artifact.model_dump(mode="json")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO recall_artifacts (
                    artifact_id,
                    query,
                    signal_ids,
                    view,
                    query_contract,
                    matches,
                    session_groups,
                    markdown_text,
                    artifact_path,
                    graph_paths,
                    provenance_contract,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["artifact_id"],
                    payload["query"],
                    _encode(payload["signal_ids"]),
                    payload["view"],
                    _encode(payload["query_contract"]),
                    _encode(payload["matches"]),
                    _encode(payload["session_groups"]),
                    payload["markdown_text"],
                    payload["artifact_path"],
                    _encode(payload["graph_paths"]),
                    _encode(payload["provenance_contract"]),
                    payload["created_at"],
                ),
            )


def _encode(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _decode(value: str) -> Any:
    return json.loads(value)


def _hydrate_journal_signal(row: sqlite3.Row | tuple[Any, ...]) -> JournalSignal:
    payload = {
        "signal_id": row[0],
        "origin_type": row[1],
        "source_name": row[2],
        "source_url": row[3],
        "source_ref": row[4],
        "raw_text": row[5],
        "raw_payload": row[6],
        "content_hash": row[7],
        "observed_at": row[8],
        "published_at": row[9],
        "captured_at": row[10],
        "agent_host": row[11],
        "agent_process": row[12],
        "agent_runtime": row[13],
        "agent_session_id": row[14],
        "agent_role": row[15],
        "workspace_path": row[16],
        "intent_status": row[17],
        "why_text": row[18],
        "who_refs": _decode(row[19]),
        "what_refs": _decode(row[20]),
        "where_refs": _decode(row[21]),
        "how_refs": _decode(row[22]),
        "graph_path": _decode(row[23]),
        "journaled_at": row[24],
    }
    return JournalSignal.model_validate(payload)
