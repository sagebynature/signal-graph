from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app
from tests.cli._journal_helpers import install_fake_journal_graph_client


def test_recall_signal_writes_markdown_artifact(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_fake_journal_graph_client(monkeypatch)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    first = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "Agent updated the deployment signal in the release notes.",
            "--origin-type",
            "agent_artifact",
            "--source-name",
            "codex",
            "--process",
            "codex",
            "--runtime-family",
            "codex",
            "--session-id",
            "session-1",
            "--what",
            "deployment",
            "--where",
            "notes/release.md",
        ],
    )
    second = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "External deployment signal confirms the rollout plan.",
            "--origin-type",
            "external_reference",
            "--source-name",
            "news",
            "--source-url",
            "https://example.com/rollout",
            "--what",
            "deployment",
            "--where",
            "https://example.com/rollout",
        ],
    )
    for raw in (first, second):
        signal_id = json.loads(raw.stdout)["signal_id"]
        assert runner.invoke(app, ["journalize-signal", "--signal", signal_id]).exit_code == 0

    result = runner.invoke(app, ["recall-signal", "--query", "deployment signal"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload["signal_ids"]) == 2
    assert "Signal Graph matched signals with provenance-rich recall." in payload["markdown_text"]
    artifact_path = Path(payload["artifact_path"])
    assert artifact_path.is_file()
