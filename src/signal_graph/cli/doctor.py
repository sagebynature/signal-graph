from __future__ import annotations

import shutil
import subprocess

import typer
from signal_graph.config import get_default_config_path


def _docker_compose_available() -> bool:
    if shutil.which("docker") is None:
        return False

    result = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def doctor() -> None:
    config_path = get_default_config_path()
    checks = {
        "config": config_path.is_file(),
        "docker": _docker_compose_available(),
        "uv": shutil.which("uv") is not None,
        "ty": shutil.which("ty") is not None,
    }
    for name, ok in checks.items():
        print(f"{name}: {'ok' if ok else 'missing'}")

    if not all(checks[name] for name in ("docker", "uv", "ty")):
        raise typer.Exit(code=1)
