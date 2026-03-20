from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

DEFAULT_PROJECT_DIR = Path(".signal-graph")
DEFAULT_CONFIG_PATH = DEFAULT_PROJECT_DIR / "config.toml"


def get_default_config_path() -> Path:
    return DEFAULT_CONFIG_PATH


def load_config(path: Path | None = None) -> dict[str, Any] | None:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return None
    try:
        with config_path.open("rb") as file:
            return tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return None


def get_neo4j_config() -> dict[str, str]:
    config = load_config() or {}
    neo4j_config = (
        config.get("neo4j", {}) if isinstance(config.get("neo4j"), dict) else {}
    )

    auth_value = os.getenv("NEO4J_AUTH")
    if auth_value:
        username, _, password = auth_value.partition("/")
    else:
        username = os.getenv(
            "NEO4J_USERNAME", str(neo4j_config.get("username", "neo4j"))
        )
        password = os.getenv(
            "NEO4J_PASSWORD", str(neo4j_config.get("password", "password"))
        )

    return {
        "uri": os.getenv(
            "NEO4J_URI", str(neo4j_config.get("uri", "neo4j://localhost:7687"))
        ),
        "username": username,
        "password": password,
        "database": os.getenv(
            "NEO4J_DATABASE", str(neo4j_config.get("database", "neo4j"))
        ),
    }
