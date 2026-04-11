from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_capture_signal_persists_journal_signal(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    result = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "Agent completed the release checklist signal.",
            "--origin-type",
            "agent_artifact",
            "--source-name",
            "codex",
            "--process",
            "codex",
            "--runtime-family",
            "codex",
            "--session-id",
            "session-a",
            "--role",
            "executor",
            "--intent-status",
            "explicit",
            "--why",
            "Safely finish the release.",
            "--what",
            "release",
            "--where",
            "notes/release.md",
            "--how",
            "checklist",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["origin_type"] == "agent_artifact"
    assert payload["agent_session_id"] == "session-a"
    assert payload["intent_status"] == "explicit"

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        row = connection.execute(
            """
            SELECT origin_type, source_name, agent_session_id, intent_status, why_text
            FROM journal_signals
            WHERE signal_id = ?
            """,
            (payload["signal_id"],),
        ).fetchone()

    assert row == (
        "agent_artifact",
        "codex",
        "session-a",
        "explicit",
        "Safely finish the release.",
    )


def test_capture_signal_rejects_why_without_explicit_intent(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    result = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "Signal with unclear why.",
            "--why",
            "This should fail.",
        ],
    )

    assert result.exit_code == 1
    assert "`why` requires --intent-status explicit or inferred" in result.stdout
