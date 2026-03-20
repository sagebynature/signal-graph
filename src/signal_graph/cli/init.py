from __future__ import annotations

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.storage.sqlite import SqliteStore


def init() -> None:
    for relative_path in ("cache", "artifacts"):
        (DEFAULT_PROJECT_DIR / relative_path).mkdir(parents=True, exist_ok=True)
    SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db").init_db()
