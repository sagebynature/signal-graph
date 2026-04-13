from __future__ import annotations

from pathlib import Path

from signal_graph.services.bootstrap import build_bootstrap_contract


def test_bootstrap_contract_entrypoints_match_runtime_surface():
    contract = build_bootstrap_contract()
    entrypoint_names = {entrypoint.name for entrypoint in contract.entrypoints}
    assert {
        "signal-graph",
        "signal-graph-mcp",
        "signal-graph mcp-server",
    } <= entrypoint_names

    smoke_commands = " ".join(
        command for step in contract.smoke_path for command in step.commands
    )
    assert "signal-graph doctor --json" in smoke_commands
    assert "signal-graph init" in smoke_commands
    assert "signal-graph recall-signal" in smoke_commands


def test_docs_reference_bootstrap_contract_and_command_surface():
    texts = {
        "readme": Path("README.md").read_text(),
        "operator": Path("docs/runbooks/operator-guide.md").read_text(),
        "docs_index": Path("docs/README.md").read_text(),
    }

    for text in texts.values():
        assert "bootstrap-describe" in text

    assert "signal-graph-mcp" in texts["readme"]
    assert "signal-graph mcp-server" in texts["operator"]
    assert "operator-guide.md" in texts["docs_index"]
