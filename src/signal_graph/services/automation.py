from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.models.automation import (
    AutomationArtifact,
    HostAutomationFlow,
    OperationalAutomationContract,
)

AUTOMATION_CONTRACT_VERSION = "2026-04-12"
AUTOMATION_DIR = DEFAULT_PROJECT_DIR / "automation"
SUPPORTED_AUTOMATION_HOSTS = ("claude-code", "codex-cli")


def build_operational_automation_contract() -> OperationalAutomationContract:
    return OperationalAutomationContract(
        contract_version=AUTOMATION_CONTRACT_VERSION,
        hosts=[
            _claude_code_flow(),
            _codex_cli_flow(),
        ],
    )


def describe_host_flow(host: str) -> HostAutomationFlow:
    normalized = _normalize_host(host)
    contract = build_operational_automation_contract()
    for flow in contract.hosts:
        if flow.host == normalized:
            return flow
    raise ValueError(f"unsupported automation host: {host}")


def install_host_integration(project_root: Path, host: str) -> dict:
    flow = describe_host_flow(host)
    automation_root = project_root / AUTOMATION_DIR
    automation_root.mkdir(parents=True, exist_ok=True)
    target_file = project_root / flow.managed_file
    target_file.parent.mkdir(parents=True, exist_ok=True)
    marker_start, marker_end = _marker_bounds(flow.managed_marker)
    managed_block = _managed_block(flow)
    original_text = target_file.read_text() if target_file.exists() else ""
    updated_text = _upsert_block(original_text, marker_start, marker_end, managed_block)
    target_file.write_text(updated_text)

    metadata_path = automation_root / f"{flow.host}.json"
    metadata = {
        "host": flow.host,
        "contract_version": flow.contract_version,
        "installed_at": datetime.now(UTC).isoformat(),
        "managed_file": flow.managed_file,
        "managed_marker": flow.managed_marker,
        "generated_artifacts": [artifact.model_dump() for artifact in flow.generated_artifacts],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")

    for artifact in flow.generated_artifacts:
        artifact_path = project_root / artifact.path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(_render_generated_artifact(flow, artifact))

    return {
        "host": flow.host,
        "status": "installed",
        "managed_file": str(target_file),
        "metadata_path": str(metadata_path),
        "generated_artifacts": [artifact.path for artifact in flow.generated_artifacts],
        "next_actions": flow.next_actions,
    }


def audit_host_integration(project_root: Path, host: str) -> dict:
    flow = describe_host_flow(host)
    target_file = project_root / flow.managed_file
    marker_start, marker_end = _marker_bounds(flow.managed_marker)
    metadata_path = project_root / AUTOMATION_DIR / f"{flow.host}.json"
    missing: list[str] = []
    if not target_file.exists():
        missing.append(flow.managed_file)
    else:
        text = target_file.read_text()
        if marker_start not in text or marker_end not in text:
            missing.append(f"managed block missing in {flow.managed_file}")

    if not metadata_path.exists():
        missing.append(str(metadata_path.relative_to(project_root)))

    for artifact in flow.generated_artifacts:
        artifact_path = project_root / artifact.path
        if not artifact_path.exists():
            missing.append(artifact.path)

    active = not missing
    return {
        "host": flow.host,
        "active": active,
        "proof_path": [
            "install/setup",
            "audit",
            "active proof",
            "uninstall/cleanup",
        ],
        "active_proof": flow.active_proof,
        "missing": missing,
        "next_actions": [] if active else flow.next_actions,
        "failure_diagnostics": [] if active else flow.failure_diagnostics,
    }


def uninstall_host_integration(project_root: Path, host: str) -> dict:
    flow = describe_host_flow(host)
    marker_start, marker_end = _marker_bounds(flow.managed_marker)
    target_file = project_root / flow.managed_file
    removed: list[str] = []
    if target_file.exists():
        text = target_file.read_text()
        cleaned = _remove_block(text, marker_start, marker_end)
        if cleaned.strip():
            target_file.write_text(cleaned)
        else:
            target_file.unlink()
        removed.append(flow.managed_file)

    metadata_path = project_root / AUTOMATION_DIR / f"{flow.host}.json"
    if metadata_path.exists():
        metadata_path.unlink()
        removed.append(str(metadata_path.relative_to(project_root)))

    for artifact in flow.generated_artifacts:
        artifact_path = project_root / artifact.path
        if artifact_path.exists():
            artifact_path.unlink()
            removed.append(artifact.path)

    return {
        "host": flow.host,
        "status": "uninstalled",
        "removed": removed,
    }


def render_operational_contract_markdown(contract: OperationalAutomationContract) -> str:
    lines = [
        "# Signal Graph Operational Automation Contract",
        "",
        f"- Contract version: `{contract.contract_version}`",
        "",
    ]
    for flow in contract.hosts:
        lines.extend(
            [
                f"## {flow.host}",
                f"- Validated: `{flow.validated}`",
                f"- Managed file: `{flow.managed_file}`",
                *[f"- Install: {step}" for step in flow.install_steps],
                *[f"- Audit: {step}" for step in flow.audit_checks],
                *[f"- Uninstall: {step}" for step in flow.uninstall_steps],
                *[f"- Active proof: {step}" for step in flow.active_proof],
                "",
            ]
        )
    return "\n".join(lines)


def _claude_code_flow() -> HostAutomationFlow:
    return HostAutomationFlow(
        host="claude-code",
        contract_version=AUTOMATION_CONTRACT_VERSION,
        validated=True,
        managed_file="CLAUDE.md",
        managed_marker="SIGNAL_GRAPH_CLAUDE_CODE",
        install_steps=[
            "Install the managed Claude Code integration block.",
            "Write host guidance artifact under .signal-graph/automation/claude-code.md.",
        ],
        audit_checks=[
            "CLAUDE.md contains the managed Signal Graph block.",
            "Automation metadata and generated artifact exist.",
        ],
        uninstall_steps=[
            "Remove managed block from CLAUDE.md.",
            "Remove host metadata and generated artifact.",
        ],
        active_proof=[
            "Managed CLAUDE.md block exists.",
            "Host guidance artifact exists.",
            "Audit output reports active=true.",
        ],
        generated_artifacts=[
            AutomationArtifact(
                path=".signal-graph/automation/claude-code.md",
                kind="guidance",
                purpose="Host-specific always-on guidance for Claude Code.",
            )
        ],
        next_actions=[
            "Run `signal-graph integration-audit --host claude-code --json`.",
            "Use `signal-graph bootstrap-describe` before asking the host to bootstrap Signal Graph.",
        ],
        failure_diagnostics=[
            "Re-run install if CLAUDE.md is missing the managed block.",
            "Verify the project root is writable if automation artifacts were not created.",
        ],
    )


def _codex_cli_flow() -> HostAutomationFlow:
    return HostAutomationFlow(
        host="codex-cli",
        contract_version=AUTOMATION_CONTRACT_VERSION,
        validated=True,
        managed_file="AGENTS.md",
        managed_marker="SIGNAL_GRAPH_CODEX_CLI",
        install_steps=[
            "Install the managed Codex CLI integration block into AGENTS.md.",
            "Write host guidance artifact under .signal-graph/automation/codex-cli.md.",
        ],
        audit_checks=[
            "AGENTS.md contains the managed Signal Graph block.",
            "Automation metadata and generated artifact exist.",
        ],
        uninstall_steps=[
            "Remove managed block from AGENTS.md.",
            "Remove host metadata and generated artifact.",
        ],
        active_proof=[
            "Managed AGENTS.md block exists.",
            "Host guidance artifact exists.",
            "Audit output reports active=true.",
        ],
        generated_artifacts=[
            AutomationArtifact(
                path=".signal-graph/automation/codex-cli.md",
                kind="guidance",
                purpose="Host-specific always-on guidance for Codex CLI.",
            )
        ],
        next_actions=[
            "Run `signal-graph integration-audit --host codex-cli --json`.",
            "Use `signal-graph bootstrap-describe` and `signal-graph recall-signal` before broad repo search.",
        ],
        failure_diagnostics=[
            "Re-run install if AGENTS.md is missing the managed block.",
            "Verify the project root is writable if automation artifacts were not created.",
        ],
    )


def _managed_block(flow: HostAutomationFlow) -> str:
    marker_start, marker_end = _marker_bounds(flow.managed_marker)
    guidance = [
        marker_start,
        f"# Signal Graph operational automation for {flow.host}",
        "",
        "Before broad repo search, consult Signal Graph's runtime contract and recall surfaces:",
        "- `uv run signal-graph bootstrap-describe`",
        "- `uv run signal-graph recall-signal --query \"<topic>\"`",
        "- `uv run signal-graph mcp-server` or `uv run signal-graph-mcp` when MCP access is needed",
        "",
        "Operational checks:",
        f"- Audit: `uv run signal-graph integration-audit --host {flow.host} --json`",
        f"- Uninstall: `uv run signal-graph integration-uninstall --host {flow.host}`",
        marker_end,
        "",
    ]
    return "\n".join(guidance)


def _render_generated_artifact(flow: HostAutomationFlow, artifact: AutomationArtifact) -> str:
    return "\n".join(
        [
            f"# Signal Graph operational guidance for {flow.host}",
            "",
            f"- Purpose: {artifact.purpose}",
            f"- Contract version: `{flow.contract_version}`",
            "",
            "## Recommended next actions",
            *[f"- {item}" for item in flow.next_actions],
            "",
            "## Active proof",
            *[f"- {item}" for item in flow.active_proof],
        ]
    )


def _marker_bounds(marker: str) -> tuple[str, str]:
    return (
        f"<!-- {marker}:START -->",
        f"<!-- {marker}:END -->",
    )


def _upsert_block(text: str, marker_start: str, marker_end: str, block: str) -> str:
    if marker_start in text and marker_end in text:
        return _remove_block(text, marker_start, marker_end).rstrip() + "\n\n" + block
    if not text.strip():
        return block
    return text.rstrip() + "\n\n" + block


def _remove_block(text: str, marker_start: str, marker_end: str) -> str:
    if marker_start not in text or marker_end not in text:
        return text
    before, _, rest = text.partition(marker_start)
    _, _, after = rest.partition(marker_end)
    cleaned = (before.rstrip() + "\n" + after.lstrip()).strip()
    return cleaned + ("\n" if cleaned else "")


def _normalize_host(host: str) -> str:
    normalized = host.strip().lower()
    if normalized not in SUPPORTED_AUTOMATION_HOSTS:
        raise ValueError(
            f"host must be one of: {', '.join(SUPPORTED_AUTOMATION_HOSTS)}"
        )
    return normalized
