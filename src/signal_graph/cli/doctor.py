from __future__ import annotations

import shutil
import subprocess

import typer
from signal_graph.config import get_default_config_path, get_neo4j_config, load_config


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


def _print_check(name: str, status: str, detail: str | None = None) -> None:
    suffix = f" ({detail})" if detail else ""
    print(f"{name}: {status}{suffix}")


def doctor() -> None:
    config_path = get_default_config_path()
    checks_ok = True

    try:
        if config_path.exists():
            load_config(config_path)
            _print_check("config", "ok")
        else:
            _print_check("config", "ok", "not present")
    except ValueError as exc:
        _print_check("config", "error", str(exc))
        checks_ok = False

    try:
        get_neo4j_config()
        _print_check("neo4j auth", "ok")
    except ValueError as exc:
        _print_check("neo4j auth", "error", str(exc))
        checks_ok = False

    runtime_checks = {
        "docker": _docker_compose_available(),
        "uv": shutil.which("uv") is not None,
    }
    for name, ok in runtime_checks.items():
        _print_check(name, "ok" if ok else "missing")
        checks_ok = checks_ok and ok

    if not checks_ok:
        raise typer.Exit(code=1)
