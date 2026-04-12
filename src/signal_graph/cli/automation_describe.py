from __future__ import annotations

import typer

from signal_graph.services.automation import (
    build_operational_automation_contract,
    describe_host_flow,
    render_operational_contract_markdown,
)


def automation_describe(
    host: str | None = typer.Option(
        None,
        "--host",
        help="Optional host selector: claude-code or codex-cli.",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        help="Output format: json or markdown.",
    ),
) -> None:
    normalized = format.strip().lower()
    if host is None:
        contract = build_operational_automation_contract()
        if normalized == "json":
            print(contract.model_dump_json(indent=2))
            return
        if normalized == "markdown":
            print(render_operational_contract_markdown(contract))
            return
        raise ValueError("format must be one of: json, markdown")

    flow = describe_host_flow(host)
    if normalized == "json":
        print(flow.model_dump_json(indent=2))
        return
    if normalized == "markdown":
        print(render_operational_contract_markdown(build_operational_automation_contract()))
        return
    raise ValueError("format must be one of: json, markdown")
