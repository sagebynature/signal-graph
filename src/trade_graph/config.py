from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

DEFAULT_PROJECT_DIR = Path(".trade-graph")
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
