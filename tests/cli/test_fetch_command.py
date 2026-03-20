from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_fetch_web_returns_raw_items_as_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(
        app,
        ["fetch", "--source", "web", "--query", "chip export restriction"],
    )

    assert result.exit_code == 0
    raw_items = json.loads(result.stdout)
    assert raw_items[0]["source_tier"] == "tier2_public"


def test_fetch_web_persists_raw_items_to_sqlite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(
        app,
        ["fetch", "--source", "web", "--query", "chip export restriction"],
    )

    assert result.exit_code == 0
    raw_item = json.loads(result.stdout)[0]
    database_path = Path(".signal-graph/signal_graph.db")

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT raw_item_id, source_tier, source_name, source_url, raw_text, raw_payload
            FROM raw_source_items
            WHERE raw_item_id = ?
            """,
            (raw_item["raw_item_id"],),
        ).fetchone()

    assert row == (
        raw_item["raw_item_id"],
        "tier2_public",
        "public_web",
        "https://example.com/search?q=chip+export+restriction",
        "Public web result for chip export restriction",
        "chip export restriction",
    )
