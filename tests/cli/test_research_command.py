from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_research_creates_bundle_for_event_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]

    result = runner.invoke(app, ["research", "--event-candidate", event_candidate_id])

    assert result.exit_code == 0
    assert "research_bundle_id" in result.stdout


def test_research_persists_bundle_for_event_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]

    result = runner.invoke(app, ["research", "--event-candidate", event_candidate_id])

    assert result.exit_code == 0
    research_bundle = json.loads(result.stdout)
    database_path = Path(".signal-graph/signal_graph.db")

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT research_bundle_id, event_candidate_id
            FROM research_bundles
            WHERE research_bundle_id = ?
            """,
            (research_bundle["research_bundle_id"],),
        ).fetchone()

    assert row == (
        research_bundle["research_bundle_id"],
        event_candidate_id,
    )
