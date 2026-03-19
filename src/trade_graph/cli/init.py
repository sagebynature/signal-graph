from __future__ import annotations

from trade_graph.config import DEFAULT_PROJECT_DIR


def init() -> None:
    for relative_path in ("cache", "artifacts"):
        (DEFAULT_PROJECT_DIR / relative_path).mkdir(parents=True, exist_ok=True)
