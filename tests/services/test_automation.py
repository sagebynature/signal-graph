from __future__ import annotations

from pathlib import Path

from signal_graph.services.automation import (
    build_operational_automation_contract,
    install_host_integration,
    audit_host_integration,
    uninstall_host_integration,
)


def test_operational_contract_lists_validated_hosts_only_for_first_wave():
    contract = build_operational_automation_contract()

    assert contract.contract_version == "2026-04-12"
    validated_hosts = [flow.host for flow in contract.hosts if flow.validated]
    assert validated_hosts == ["claude-code", "codex-cli"]


def test_install_audit_uninstall_round_trip_for_claude_code(tmp_path):
    (tmp_path / ".signal-graph").mkdir()

    installed = install_host_integration(tmp_path, "claude-code")
    assert installed["status"] == "installed"
    assert (tmp_path / "CLAUDE.md").is_file()

    audited = audit_host_integration(tmp_path, "claude-code")
    assert audited["active"] is True
    assert audited["missing"] == []

    uninstalled = uninstall_host_integration(tmp_path, "claude-code")
    assert uninstalled["status"] == "uninstalled"
    assert not (tmp_path / ".signal-graph" / "automation" / "claude-code.json").exists()

    post_audit = audit_host_integration(tmp_path, "claude-code")
    assert post_audit["active"] is False
    assert post_audit["missing"]


def test_install_is_idempotent_for_codex_cli(tmp_path):
    (tmp_path / ".signal-graph").mkdir()

    first = install_host_integration(tmp_path, "codex-cli")
    second = install_host_integration(tmp_path, "codex-cli")

    assert first["generated_artifacts"] == second["generated_artifacts"]
    agents_text = (tmp_path / "AGENTS.md").read_text()
    assert agents_text.count("SIGNAL_GRAPH_CODEX_CLI:START") == 1


def test_uninstall_does_not_remove_unrelated_content(tmp_path):
    (tmp_path / ".signal-graph").mkdir()
    (tmp_path / "AGENTS.md").write_text("# Existing instructions\n")
    install_host_integration(tmp_path, "codex-cli")

    uninstall_host_integration(tmp_path, "codex-cli")

    assert (tmp_path / "AGENTS.md").read_text() == "# Existing instructions\n"
