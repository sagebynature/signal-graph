from __future__ import annotations

import json

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_bootstrap_describe_outputs_valid_json_contract(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["bootstrap-describe"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["contract_version"] == "2026-04-11"
    assert payload["entrypoints"]
    assert payload["mcp"]["transport"] == "stdio"
    assert payload["smoke_path"]
    assert payload["proof_outputs"]
    assert payload["next_actions"]


def test_bootstrap_describe_outputs_markdown(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["bootstrap-describe", "--format", "markdown"])

    assert result.exit_code == 0
    assert "# Signal Graph Agent Bootstrap Contract" in result.stdout
    assert "signal-graph-mcp" in result.stdout
    assert "doctor --json" in result.stdout


def test_doctor_json_output_is_machine_readable(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["overall_ok"] is True
    assert payload["checks"]["config"]["status"] == "ok"
    assert payload["checks"]["uv"]["status"] == "ok"
