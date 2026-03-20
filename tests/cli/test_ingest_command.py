from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_ingest_creates_graph_event_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    runner.invoke(app, ["research", "--event-candidate", event_candidate_id])

    result = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])

    assert result.exit_code == 0
    assert "graph_event_id" in result.stdout


def test_ingest_persists_graph_event_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    runner.invoke(app, ["research", "--event-candidate", event_candidate_id])

    result = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])

    assert result.exit_code == 0
    graph_event = json.loads(result.stdout)
    database_path = Path(".trade-graph/trade_graph.db")

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT graph_event_id, event_candidate_id
            FROM graph_events
            WHERE graph_event_id = ?
            """,
            (graph_event["graph_event_id"],),
        ).fetchone()

    assert row == (
        graph_event["graph_event_id"],
        event_candidate_id,
    )
