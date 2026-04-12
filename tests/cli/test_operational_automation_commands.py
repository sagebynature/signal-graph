from __future__ import annotations

import json

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_automation_describe_outputs_contract(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0

    result = runner.invoke(app, ["automation-describe"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["contract_version"] == "2026-04-12"
    assert len(payload["hosts"]) == 2


def test_integration_install_audit_uninstall_for_claude_code(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0

    install = runner.invoke(app, ["integration-install", "--host", "claude-code"])
    assert install.exit_code == 0
    install_payload = json.loads(install.stdout)
    assert install_payload["status"] == "installed"

    audit = runner.invoke(app, ["integration-audit", "--host", "claude-code", "--json"])
    assert audit.exit_code == 0
    audit_payload = json.loads(audit.stdout)
    assert audit_payload["active"] is True

    uninstall = runner.invoke(app, ["integration-uninstall", "--host", "claude-code"])
    assert uninstall.exit_code == 0
    uninstall_payload = json.loads(uninstall.stdout)
    assert uninstall_payload["status"] == "uninstalled"
