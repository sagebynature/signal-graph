from __future__ import annotations

import json
import shutil
import subprocess

import typer
from signal_graph.config import (
    get_explicit_neo4j_auth,
    get_default_config_path,
    get_neo4j_config,
    load_config,
)


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


def doctor(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable doctor output.",
    ),
) -> None:
    config_path = get_default_config_path()
    checks_ok = True
    config_valid = True
    explicit_auth_valid = False
    results: dict[str, dict[str, str]] = {}

    def record(name: str, status: str, detail: str | None = None) -> None:
        results[name] = {"status": status, "detail": detail or ""}
        if not json_output:
            _print_check(name, status, detail)

    try:
        if config_path.exists():
            load_config(config_path)
            record("config", "ok")
        else:
            record("config", "ok", "not present")
    except ValueError as exc:
        record("config", "error", str(exc))
        checks_ok = False
        config_valid = False

    try:
        explicit_auth_valid = get_explicit_neo4j_auth() is not None
    except ValueError as exc:
        record("neo4j auth", "error", str(exc))
        checks_ok = False
    else:
        if config_valid:
            try:
                get_neo4j_config()
                record("neo4j auth", "ok")
            except ValueError as exc:
                record("neo4j auth", "error", str(exc))
                checks_ok = False
        elif explicit_auth_valid:
            record("neo4j auth", "blocked", "config invalid")
        else:
            record("neo4j auth", "skipped", "config invalid")

    runtime_checks = {
        "docker": _docker_compose_available(),
        "uv": shutil.which("uv") is not None,
    }
    for name, ok in runtime_checks.items():
        record(name, "ok" if ok else "missing")
        checks_ok = checks_ok and ok

    if json_output:
        print(json.dumps({"overall_ok": checks_ok, "checks": results}))

    if not checks_ok:
        raise typer.Exit(code=1)
