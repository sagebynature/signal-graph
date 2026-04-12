from __future__ import annotations

import json
from pathlib import Path

import typer

from signal_graph.services.automation import audit_host_integration


def integration_audit(
    host: str = typer.Option(..., "--host", help="Target host: claude-code or codex-cli."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable audit output.",
    ),
) -> None:
    result = audit_host_integration(Path.cwd(), host)
    if json_output:
        print(json.dumps(result))
        return
    print(result)
