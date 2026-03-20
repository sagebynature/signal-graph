from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_explain_outputs_memo_sections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["explain", "--event", "ge-1", "--candidate", "SMH"])

    assert result.exit_code == 0
    assert "Confirmed fact" in result.stdout
    assert "Graph implication" in result.stdout


def test_explain_writes_markdown_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["explain", "--event", "ge-1", "--candidate", "SMH"])

    assert result.exit_code == 0
    artifact_path = Path(".signal-graph/artifacts/ge-1-SMH.md")
    assert artifact_path.is_file()
    assert "Assistant inference" in artifact_path.read_text()
