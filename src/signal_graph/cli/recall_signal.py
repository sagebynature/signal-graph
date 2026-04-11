from __future__ import annotations

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.journal import recall_signals
from signal_graph.storage.sqlite import SqliteStore


def recall_signal(
    query: str = typer.Option(
        ...,
        "--query",
        help="Recall query used to search journal signals.",
    ),
    limit: int = typer.Option(
        5,
        "--limit",
        min=1,
        max=20,
        help="Maximum number of matching signals to include.",
    ),
) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    artifact = recall_signals(
        store,
        query=query,
        artifact_dir=DEFAULT_PROJECT_DIR / "artifacts",
        limit=limit,
    )
    print(artifact.model_dump_json())
