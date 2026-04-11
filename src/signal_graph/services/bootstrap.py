from __future__ import annotations

from signal_graph.models.bootstrap import (
    BootstrapCommand,
    BootstrapContract,
    BootstrapMcpContract,
    BootstrapStep,
)
from signal_graph.mcp.server import build_tool_definitions

BOOTSTRAP_CONTRACT_VERSION = "2026-04-11"


def build_bootstrap_contract() -> BootstrapContract:
    mcp_tools = sorted(tool["name"] for tool in build_tool_definitions())
    return BootstrapContract(
        contract_version=BOOTSTRAP_CONTRACT_VERSION,
        entrypoints=[
            BootstrapCommand(
                name="signal-graph",
                command=["signal-graph"],
                purpose="Primary CLI entrypoint for doctor, init, journal, recall, and bootstrap discovery.",
            ),
            BootstrapCommand(
                name="signal-graph-mcp",
                command=["signal-graph-mcp"],
                purpose="Published stdio MCP entrypoint for host integrations.",
            ),
            BootstrapCommand(
                name="signal-graph mcp-server",
                command=["signal-graph", "mcp-server"],
                purpose="Alternate stdio MCP launch path through the primary CLI.",
            ),
        ],
        prereqs=["Python 3.12", "uv", "Docker", "Neo4j runtime availability"],
        env=[
            "NEO4J_AUTH=username/password (optional override before first Neo4j startup)",
            ".signal-graph/config.toml (optional local config)",
        ],
        project_state=[
            ".signal-graph/signal_graph.db created by `signal-graph init`",
            ".signal-graph/artifacts/ created for memo and recall output",
            ".signal-graph/cache/ created for local runtime material",
        ],
        smoke_path=[
            BootstrapStep(
                id="doctor",
                title="Verify prerequisites and config",
                commands=["signal-graph doctor --json"],
                expected_outputs=[
                    "overall_ok=true",
                    "checks.config.status in {ok}",
                    "checks.uv.status in {ok}",
                ],
            ),
            BootstrapStep(
                id="init",
                title="Initialize local project state",
                commands=["signal-graph init"],
                expected_outputs=[
                    ".signal-graph/signal_graph.db exists",
                    ".signal-graph/artifacts/ exists",
                ],
            ),
            BootstrapStep(
                id="journal-smoke",
                title="Run a minimal journal capture/recall proof",
                commands=[
                    "signal-graph capture-signal --text 'bootstrap smoke signal' --origin-type user --source-name manual --what bootstrap",
                    "signal-graph journalize-signal --signal <signal_id>",
                    "signal-graph recall-signal --query bootstrap",
                ],
                expected_outputs=[
                    "capture-signal returns stable JSON with signal_id",
                    "journalize-signal returns graph_path and journaled_at",
                    "recall-signal returns structured JSON plus markdown recall artifact",
                ],
            ),
            BootstrapStep(
                id="mcp-startup",
                title="Confirm MCP server startup contract",
                commands=[
                    "signal-graph bootstrap-describe --format json",
                    "signal-graph-mcp  # stdio server for initialize/tools/list handshake",
                ],
                expected_outputs=[
                    "bootstrap contract includes launch command, proof methods, expected tools, and next actions",
                    "MCP initialize/tools-list handshake exposes the documented tool names",
                ],
            ),
        ],
        mcp=BootstrapMcpContract(
            launch_command=["signal-graph-mcp"],
            host_agnostic_assumptions=[
                "Uses stdio transport",
                "Client performs initialize then tools/list",
                "No host-specific plugin framework is required",
            ],
            proof_methods=["initialize", "tools/list"],
            expected_tools=mcp_tools,
        ),
        proof_outputs=[
            "doctor returns machine-readable readiness data",
            "init creates local project directories and SQLite state",
            "journal smoke path yields a signal id, graph path, and recall artifact",
            "MCP contract declares launch command, proof methods, and expected tools",
        ],
        next_actions=[
            "If doctor fails, fix prerequisites or config first.",
            "If init succeeds, capture and journal a signal before expecting strong recall.",
            "If MCP startup is needed, use signal-graph-mcp or signal-graph mcp-server.",
            "After smoke success, continue with capture-signal or recall-signal depending on workflow needs.",
        ],
        drift_checks=[
            "Bootstrap contract entrypoints must match CLI and published scripts.",
            "README/runbooks/help text must stay aligned with the bootstrap contract.",
            "MCP expected tool names must match the runtime server implementation.",
        ],
        provenance_rules=[
            "Do not invent `why`; unknown intent is better than fabricated intent.",
            "Preserve provenance and losslessness during bootstrap smoke checks.",
            "CLI and MCP recall semantics must remain aligned.",
        ],
    )


def render_bootstrap_contract_markdown(contract: BootstrapContract) -> str:
    lines = [
        "# Signal Graph Agent Bootstrap Contract",
        "",
        f"- Contract version: `{contract.contract_version}`",
        "",
        "## Entrypoints",
    ]
    for entrypoint in contract.entrypoints:
        lines.extend(
            [
                "",
                f"### {entrypoint.name}",
                f"- Command: `{' '.join(entrypoint.command)}`",
                f"- Purpose: {entrypoint.purpose}",
            ]
        )
    lines.extend(["", "## Smoke Path"])
    for step in contract.smoke_path:
        lines.extend(
            [
                "",
                f"### {step.id}: {step.title}",
                *[f"- Command: `{command}`" for command in step.commands],
                *[f"- Expected output: {output}" for output in step.expected_outputs],
            ]
        )
    lines.extend(
        [
            "",
            "## MCP",
            f"- Transport: `{contract.mcp.transport}`",
            f"- Launch command: `{' '.join(contract.mcp.launch_command)}`",
            *[f"- Assumption: {item}" for item in contract.mcp.host_agnostic_assumptions],
            *[f"- Proof method: `{item}`" for item in contract.mcp.proof_methods],
            f"- Expected tools: {', '.join(contract.mcp.expected_tools)}",
            "",
            "## Next Actions",
            *[f"- {item}" for item in contract.next_actions],
        ]
    )
    return "\n".join(lines)
