from __future__ import annotations

import json
from pathlib import Path

import typer

from signal_graph.services.automation import uninstall_host_integration


def integration_uninstall(
    host: str = typer.Option(..., "--host", help="Target host: claude-code or codex-cli."),
) -> None:
    result = uninstall_host_integration(Path.cwd(), host)
    print(json.dumps(result))
