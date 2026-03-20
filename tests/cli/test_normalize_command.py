from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_normalize_requires_initialized_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["normalize", "--raw-item", "raw-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Project is not initialized. Run `signal-graph init` first."
    )


def test_normalize_requires_database_file_in_initialized_project_dir(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    Path(".signal-graph").mkdir()

    runner = CliRunner()
    result = runner.invoke(app, ["normalize", "--raw-item", "raw-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Project is not initialized. Run `signal-graph init` first."
    )


def test_normalize_help_describes_raw_item_identifier():
    runner = CliRunner()

    result = runner.invoke(app, ["normalize", "--help"])

    assert result.exit_code == 0
    assert "Raw source item id to normalize." in result.stdout


def test_normalize_creates_event_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]

    result = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])

    assert result.exit_code == 0
    assert "event_candidate_id" in result.stdout


def test_normalize_accepts_event_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "TSMC cuts capex"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]

    result = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "capex_cut",
            "--direction",
            "negative",
            "--primary-entity",
            "TSMC",
            "--secondary-entity",
            "SMH",
        ],
    )

    assert result.exit_code == 0
    event_candidate = json.loads(result.stdout)
    assert event_candidate["event_type"] == "capex_cut"
    assert event_candidate["direction"] == "negative"
    assert event_candidate["primary_entities"] == ["TSMC"]
    assert event_candidate["secondary_entities"] == ["SMH"]


def test_normalize_dedupes_matching_titles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    first_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    second_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])

    first_raw_item_id = json.loads(first_submit.stdout)["raw_item_id"]
    second_raw_item_id = json.loads(second_submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(app, ["normalize", "--raw-item", first_raw_item_id])
    second_normalize = runner.invoke(
        app, ["normalize", "--raw-item", second_raw_item_id]
    )

    assert first_normalize.exit_code == 0
    assert second_normalize.exit_code == 0
    assert (
        json.loads(first_normalize.stdout)["event_candidate_id"]
        == json.loads(second_normalize.stdout)["event_candidate_id"]
    )


def test_normalize_merges_source_item_ids_for_duplicate_events(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    first_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    second_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])

    first_raw_item_id = json.loads(first_submit.stdout)["raw_item_id"]
    second_raw_item_id = json.loads(second_submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            first_raw_item_id,
            "--event-type",
            "supplier_disruption",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
        ],
    )
    second_normalize = runner.invoke(
        app, ["normalize", "--raw-item", second_raw_item_id]
    )

    assert first_normalize.exit_code == 0
    assert second_normalize.exit_code == 0

    event_candidate = json.loads(second_normalize.stdout)
    assert sorted(event_candidate["source_item_ids"]) == sorted(
        [first_raw_item_id, second_raw_item_id]
    )
    assert event_candidate["event_type"] == "supplier_disruption"
    assert event_candidate["direction"] == "negative"
    assert event_candidate["primary_entities"] == ["NVDA"]

    database_path = Path(".signal-graph/signal_graph.db")
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT source_item_ids, event_type, direction, primary_entities
            FROM event_candidates
            WHERE event_candidate_id = ?
            """,
            (event_candidate["event_candidate_id"],),
        ).fetchone()

    assert row == (
        json.dumps(sorted([first_raw_item_id, second_raw_item_id])),
        "supplier_disruption",
        "negative",
        json.dumps(["NVDA"]),
    )
