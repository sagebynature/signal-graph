from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_submit_stores_manual_raw_item(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["submit", "--text", "TSMC cuts capex"])

    assert result.exit_code == 0
    assert "raw_item_id" in result.stdout


def test_submit_persists_raw_item_to_sqlite(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["submit", "--text", "TSMC cuts capex"])

    assert result.exit_code == 0

    raw_item = json.loads(result.stdout)
    database_path = Path(".signal-graph/signal_graph.db")

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT raw_item_id, source_tier, source_name, raw_text "
            "FROM raw_source_items WHERE raw_item_id = ?",
            (raw_item["raw_item_id"],),
        ).fetchone()

    assert row == (
        raw_item["raw_item_id"],
        "tier3_manual",
        "manual",
        "TSMC cuts capex",
    )
