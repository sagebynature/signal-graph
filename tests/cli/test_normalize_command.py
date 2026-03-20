from __future__ import annotations

import json

from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_normalize_creates_event_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]

    result = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])

    assert result.exit_code == 0
    assert "event_candidate_id" in result.stdout


def test_normalize_dedupes_matching_titles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    first_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    second_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])

    first_raw_item_id = json.loads(first_submit.stdout)["raw_item_id"]
    second_raw_item_id = json.loads(second_submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(app, ["normalize", "--raw-item", first_raw_item_id])
    second_normalize = runner.invoke(app, ["normalize", "--raw-item", second_raw_item_id])

    assert first_normalize.exit_code == 0
    assert second_normalize.exit_code == 0
    assert json.loads(first_normalize.stdout)["event_candidate_id"] == json.loads(
        second_normalize.stdout
    )["event_candidate_id"]
