from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_init_creates_local_directories(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert Path(".signal-graph/cache").is_dir()
    assert Path(".signal-graph/artifacts").is_dir()
    assert Path(".signal-graph/signal_graph.db").is_file()
