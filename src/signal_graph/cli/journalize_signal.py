from __future__ import annotations

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.journal import journalize_signal as journalize_signal_service
from signal_graph.storage.sqlite import SqliteStore


def journalize_signal(
    signal: str = typer.Option(
        ...,
        "--signal",
        help="Journal signal id to journalize into the graph topology.",
    )
) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    journalized = journalize_signal_service(store, signal)
    print(journalized.model_dump_json())
