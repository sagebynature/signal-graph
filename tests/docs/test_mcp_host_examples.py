from __future__ import annotations

import json
from pathlib import Path

from signal_graph.services.bootstrap import build_bootstrap_contract


def test_host_matrix_has_expected_statuses_and_evidence_fields():
    payload = json.loads(Path("docs/integrations/mcp-host-matrix.json").read_text())
    hosts = payload["hosts"]
    assert payload["version"]
    validated_hosts = {host["host"] for host in hosts if host["status"] == "validated"}
    assert validated_hosts == {"Claude Code", "Codex CLI"}
    assert any(host["status"] == "example-only" for host in hosts)
    assert any(host["status"] == "deferred" for host in hosts)
    for host in hosts:
        assert host["config_example_path"]
        assert host["evidence_path"]
        assert host["validation_date"]
        assert host["revalidation_policy"]


def test_host_examples_reference_runtime_entrypoints():
    contract = build_bootstrap_contract()
    runtime_commands = {tuple(entry["command"]) for entry in contract.model_dump()["entrypoints"]}
    claude_example = json.loads(Path("docs/examples/mcp/claude-code-local.json").read_text())
    claude_desktop_example = json.loads(Path("docs/examples/mcp/claude-desktop.json").read_text())
    cursor_example = json.loads(Path("docs/examples/mcp/cursor-mcp.json").read_text())
    codex_example = Path("docs/examples/mcp/codex-cli.md").read_text()

    assert tuple(claude_example["args"]) == ("-m", "signal_graph.mcp.server")
    assert tuple(claude_desktop_example["mcpServers"]["signal-graph"]["args"]) == (
        "-m",
        "signal_graph.mcp.server",
    )
    assert tuple(cursor_example["mcpServers"]["signal-graph"]["args"]) == (
        "-m",
        "signal_graph.mcp.server",
    )
    assert any(command[0] == "signal-graph-mcp" or command[:2] == ("signal-graph", "mcp-server") for command in runtime_commands)
    assert "codex mcp add signal-graph" in codex_example


def test_integration_docs_reference_matrix_and_examples():
    text = Path("docs/integrations/README.md").read_text()
    assert "mcp-host-matrix.json" in text
    assert "docs/examples/mcp/" in text
    assert "Claude Desktop" in text
