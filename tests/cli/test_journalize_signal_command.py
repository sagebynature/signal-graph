from __future__ import annotations

import json

from typer.testing import CliRunner

from signal_graph.cli.main import app
from tests.cli._journal_helpers import install_fake_journal_graph_client


def test_journalize_signal_adds_graph_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_fake_journal_graph_client(monkeypatch)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    capture = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "User noted a deployment signal.",
            "--origin-type",
            "user",
            "--source-name",
            "manual",
            "--what",
            "deployment",
            "--where",
            "notes/deploy.md",
        ],
    )
    signal_id = json.loads(capture.stdout)["signal_id"]

    result = runner.invoke(app, ["journalize-signal", "--signal", signal_id])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["signal_id"] == signal_id
    assert payload["graph_path"] == ["SIGNAL", "ORIGIN:USER", "WHAT", "WHEN", "WHERE"]
    assert payload["journaled_at"] is not None
