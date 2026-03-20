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
    except tomllib.TOMLDecodeError as exc:
        message = f"Invalid config TOML at {config_path}: {exc}"
        raise ValueError(message) from exc
    except OSError as exc:
        message = f"Unable to read config at {config_path}: {exc}"
        raise ValueError(message) from exc


def get_scoring_policy_config() -> dict[str, Any] | None:
    config = load_config() or {}
    scoring_policy = config.get("scoring_policy")
    return scoring_policy if isinstance(scoring_policy, dict) else None


def parse_neo4j_auth(auth_value: str | None) -> tuple[str, str] | None:
    if auth_value is None:
        return None

    if auth_value == "":
        message = "NEO4J_AUTH must use username/password format with non-empty values"
        raise ValueError(message)

    username, separator, password = auth_value.partition("/")
    if separator != "/" or not username or not password:
        message = "NEO4J_AUTH must use username/password format with non-empty values"
        raise ValueError(message)

    return username, password


def validate_neo4j_credentials(username: str, password: str) -> tuple[str, str]:
    if not username or not password:
        message = "Neo4j username and password must be non-empty"
        raise ValueError(message)

    return username, password


def get_explicit_neo4j_auth() -> tuple[str, str] | None:
    if "NEO4J_AUTH" in os.environ:
        return parse_neo4j_auth(os.environ.get("NEO4J_AUTH"))

    if "NEO4J_USERNAME" in os.environ or "NEO4J_PASSWORD" in os.environ:
        return validate_neo4j_credentials(
            os.environ.get("NEO4J_USERNAME", ""),
            os.environ.get("NEO4J_PASSWORD", ""),
        )

    return None


def get_neo4j_config() -> dict[str, str]:
    config = load_config() or {}
    neo4j_config = (
        config.get("neo4j", {}) if isinstance(config.get("neo4j"), dict) else {}
    )

    auth = parse_neo4j_auth(os.getenv("NEO4J_AUTH"))
    if auth is not None:
        username, password = auth
    else:
        username = os.getenv(
            "NEO4J_USERNAME", str(neo4j_config.get("username", "neo4j"))
        )
        password = os.getenv(
            "NEO4J_PASSWORD", str(neo4j_config.get("password", "password"))
        )
        username, password = validate_neo4j_credentials(username, password)

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
