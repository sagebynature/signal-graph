from __future__ import annotations

from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_fetch_web_returns_raw_items(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(
        app,
        ["fetch", "--source", "web", "--query", "chip export restriction"],
    )

    assert result.exit_code == 0
    assert "source_tier" in result.stdout
