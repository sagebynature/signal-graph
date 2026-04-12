from __future__ import annotations

import json
from pathlib import Path

import typer

from signal_graph.services.automation import install_host_integration


def integration_install(
    host: str = typer.Option(..., "--host", help="Target host: claude-code or codex-cli."),
) -> None:
    result = install_host_integration(Path.cwd(), host)
    print(json.dumps(result))
